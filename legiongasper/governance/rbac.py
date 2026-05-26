import asyncio
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto

class Permission(Enum):
    
    AGENT_SPAWN = "agent:spawn"
    AGENT_TERMINATE = "agent:terminate"
    AGENT_VIEW = "agent:view"
    
    TASK_SUBMIT = "task:submit"
    TASK_CANCEL = "task:cancel"
    TASK_VIEW = "task:view"
    
    TOOL_USE_PUBLIC = "tool:use:public"
    TOOL_USE_RESTRICTED = "tool:use:restricted"
    TOOL_USE_ADMIN = "tool:use:admin"
    
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    
    AUDIT_VIEW = "audit:view"
    COST_VIEW = "cost:view"
    COST_MANAGE = "cost:manage"
    RBAC_MANAGE = "rbac:manage"
    
    SYSTEM_CONFIG = "system:config"
    SYSTEM_SHUTDOWN = "system:shutdown"

@dataclass
class Role:
    
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits: Optional[str] = None

class RBACManager:
    
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._assignments: Dict[str, Set[str]] = {}  
        self._lock = asyncio.Lock()
        
        self._init_default_roles()
    
    def _init_default_roles(self):
        
        self._roles["guest"] = Role(
            name="guest",
            description="Unauthenticated users",
            permissions={Permission.AGENT_VIEW, Permission.TASK_VIEW}
        )
        
        self._roles["user"] = Role(
            name="user",
            description="Standard users",
            permissions={
                Permission.AGENT_SPAWN,
                Permission.AGENT_VIEW,
                Permission.TASK_SUBMIT,
                Permission.TASK_VIEW,
                Permission.TASK_CANCEL,
                Permission.TOOL_USE_PUBLIC,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.COST_VIEW
            }
        )
        
        self._roles["developer"] = Role(
            name="developer",
            description="Developers with extended access",
            permissions={
                Permission.AGENT_SPAWN,
                Permission.AGENT_TERMINATE,
                Permission.AGENT_VIEW,
                Permission.TASK_SUBMIT,
                Permission.TASK_VIEW,
                Permission.TASK_CANCEL,
                Permission.TOOL_USE_PUBLIC,
                Permission.TOOL_USE_RESTRICTED,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.MEMORY_DELETE,
                Permission.AUDIT_VIEW,
                Permission.COST_VIEW
            }
        )
        
        self._roles["admin"] = Role(
            name="admin",
            description="Administrators with full access",
            permissions=set(Permission)  
        )
        
        self._roles["agent"] = Role(
            name="agent",
            description="Autonomous agents",
            permissions={
                Permission.AGENT_VIEW,
                Permission.TASK_VIEW,
                Permission.TOOL_USE_PUBLIC,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE
            }
        )
        
        self._roles["captain"] = Role(
            name="captain",
            description="Captain agents",
            permissions={
                Permission.AGENT_SPAWN,
                Permission.AGENT_TERMINATE,
                Permission.AGENT_VIEW,
                Permission.TASK_SUBMIT,
                Permission.TASK_VIEW,
                Permission.TASK_CANCEL,
                Permission.TOOL_USE_PUBLIC,
                Permission.TOOL_USE_RESTRICTED,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE
            }
        )
    
    def create_role(self, role: Role):
        
        self._roles[role.name] = role
    
    def get_role(self, name: str) -> Optional[Role]:
        
        return self._roles.get(name)
    
    def list_roles(self) -> List[str]:
        
        return list(self._roles.keys())
    
    async def assign_role(self, actor_id: str, role_name: str):
        
        if role_name not in self._roles:
            raise ValueError(f"Role not found: {role_name}")
        
        async with self._lock:
            if actor_id not in self._assignments:
                self._assignments[actor_id] = set()
            self._assignments[actor_id].add(role_name)
    
    async def remove_role(self, actor_id: str, role_name: str):
        
        async with self._lock:
            if actor_id in self._assignments:
                self._assignments[actor_id].discard(role_name)
    
    async def get_actor_roles(self, actor_id: str) -> List[str]:
        
        async with self._lock:
            return list(self._assignments.get(actor_id, set()))
    
    async def check_permission(self, 
                               actor_id: str,
                               permission: Permission) -> bool:
        
        async with self._lock:
            roles = self._assignments.get(actor_id, set())
            
            for role_name in roles:
                role = self._roles.get(role_name)
                if role and permission in role.permissions:
                    return True
            
            return False
    
    async def check_permissions(self,
                               actor_id: str,
                               permissions: List[Permission],
                               require_all: bool = True) -> bool:
        
        if require_all:
            for perm in permissions:
                if not await self.check_permission(actor_id, perm):
                    return False
            return True
        else:
            for perm in permissions:
                if await self.check_permission(actor_id, perm):
                    return True
            return False
    
    async def get_actor_permissions(self, actor_id: str) -> Set[Permission]:
        
        async with self._lock:
            roles = self._assignments.get(actor_id, set())
            permissions = set()
            
            for role_name in roles:
                role = self._roles.get(role_name)
                if role:
                    permissions.update(role.permissions)
            
            return permissions
    
    def require_permission(self, permission: Permission):
        
        def decorator(func):
            async def wrapper(*args, **kwargs):
                
                actor_id = kwargs.get('actor_id') or (args[0] if args else None)
                
                if not actor_id:
                    raise PermissionError("actor_id required")
                
                has_perm = await self.check_permission(actor_id, permission)
                if not has_perm:
                    raise PermissionError(
                        f"Actor {actor_id} lacks permission {permission.value}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator

_rbac: Optional[RBACManager] = None

def get_rbac_manager() -> RBACManager:
    
    global _rbac
    if _rbac is None:
        _rbac = RBACManager()
    return _rbac