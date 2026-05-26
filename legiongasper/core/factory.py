import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import logging

from .agent import Agent
from ..config import AgentTemplate, get_template_registry, get_settings

class AgentStatus(Enum):
    
    AVAILABLE = "available"
    BUSY = "busy"
    IDLE = "idle"
    TERMINATED = "terminated"

class PooledAgent:
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.status = AgentStatus.IDLE
        self.acquired_at: Optional[datetime] = None
        self.task_count = 0
        self.created_at = datetime.utcnow()
    
    def acquire(self):
        
        self.status = AgentStatus.BUSY
        self.acquired_at = datetime.utcnow()
    
    def release(self):
        
        self.status = AgentStatus.IDLE
        self.acquired_at = None
        self.task_count += 1
    
    def terminate(self):
        
        self.status = AgentStatus.TERMINATED

class AgentFactory:
    
    def __init__(self):
        self.settings = get_settings()
        self.template_registry = get_template_registry()
        
        self._pools: Dict[str, List[PooledAgent]] = {}
        
        self._agents: Dict[str, PooledAgent] = {}
        
        self._pool_lock = asyncio.Lock()
        self._spawn_semaphore = asyncio.Semaphore(self.settings.parallel_executions)
        
        self._spawn_count = 0
        self._destroy_count = 0
        
        self._logger = logging.getLogger(__name__)
    
    async def spawn(self, 
                   template_id: str,
                   session_id: Optional[str] = None,
                   use_pool: bool = True) -> Agent:
        
        template = self.template_registry.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        if use_pool:
            pooled = await self._acquire_from_pool(template_id)
            if pooled:
                pooled.acquire()
                self._logger.info(f"Reused agent {pooled.agent.agent_id} from pool")
                return pooled.agent
        
        async with self._spawn_semaphore:
            agent = Agent(
                template=template,
                session_id=session_id or f"session_{uuid.uuid4().hex[:8]}"
            )
            
            await agent.initialize()
            
            pooled = PooledAgent(agent)
            pooled.acquire()
            
            async with self._pool_lock:
                self._agents[agent.agent_id] = pooled
                if template_id not in self._pools:
                    self._pools[template_id] = []
                self._pools[template_id].append(pooled)
            
            self._spawn_count += 1
            self._logger.info(f"Spawned new agent {agent.agent_id} from template {template_id}")
            
            return agent
    
    async def _acquire_from_pool(self, template_id: str) -> Optional[PooledAgent]:
        
        async with self._pool_lock:
            if template_id not in self._pools:
                return None
            
            for pooled in self._pools[template_id]:
                if pooled.status == AgentStatus.IDLE:
                    return pooled
            
            return None
    
    async def release(self, agent_id: str):
        
        async with self._pool_lock:
            pooled = self._agents.get(agent_id)
            if pooled:
                pooled.release()
                self._logger.debug(f"Released agent {agent_id} back to pool")
    
    async def destroy(self, agent_id: str):
        
        async with self._pool_lock:
            pooled = self._agents.get(agent_id)
            if pooled:
                await pooled.agent.terminate()
                pooled.terminate()
                
                template_id = pooled.agent.template.template_id
                if template_id in self._pools:
                    self._pools[template_id] = [
                        p for p in self._pools[template_id] 
                        if p.agent.agent_id != agent_id
                    ]
                
                del self._agents[agent_id]
                self._destroy_count += 1
                self._logger.info(f"Destroyed agent {agent_id}")
    
    async def spawn_squad(self,
                         template_ids: List[str],
                         session_id: Optional[str] = None) -> List[Agent]:
        
        if not session_id:
            session_id = f"squad_session_{uuid.uuid4().hex[:8]}"
        
        tasks = [
            self.spawn(tid, session_id=session_id)
            for tid in template_ids
        ]
        
        agents = await asyncio.gather(*tasks)
        return list(agents)
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        
        async with self._pool_lock:
            pooled = self._agents.get(agent_id)
            return pooled.agent if pooled else None
    
    async def get_pooled_agent(self, agent_id: str) -> Optional[PooledAgent]:
        
        async with self._pool_lock:
            return self._agents.get(agent_id)
    
    async def list_agents(self, 
                         template_id: Optional[str] = None,
                         status: Optional[AgentStatus] = None) -> List[Dict[str, Any]]:
        
        async with self._pool_lock:
            results = []
            for pooled in self._agents.values():
                if template_id and pooled.agent.template.template_id != template_id:
                    continue
                if status and pooled.status != status:
                    continue
                
                results.append({
                    "agent_id": pooled.agent.agent_id,
                    "template_id": pooled.agent.template.template_id,
                    "status": pooled.status.value,
                    "task_count": pooled.task_count,
                    "created_at": pooled.created_at.isoformat()
                })
            return results
    
    async def cleanup_pool(self, 
                          template_id: Optional[str] = None,
                          max_idle: int = 5):
        
        async with self._pool_lock:
            templates = [template_id] if template_id else list(self._pools.keys())
            
            for tid in templates:
                if tid not in self._pools:
                    continue
                
                idle = [
                    p for p in self._pools[tid]
                    if p.status == AgentStatus.IDLE
                ]
                
                to_remove = idle[max_idle:]
                for pooled in to_remove:
                    await pooled.agent.terminate()
                    pooled.terminate()
                    del self._agents[pooled.agent.agent_id]
                
                self._pools[tid] = [
                    p for p in self._pools[tid]
                    if p.status != AgentStatus.TERMINATED
                ]
                
                self._logger.info(f"Cleaned up {len(to_remove)} idle agents from {tid} pool")
    
    async def health_check(self) -> Dict[str, Any]:
        
        async with self._pool_lock:
            healthy = 0
            unhealthy = 0
            
            for pooled in self._agents.values():
                try:
                    
                    info = pooled.agent.get_info()
                    if info["state"] != "terminated":
                        healthy += 1
                    else:
                        unhealthy += 1
                except Exception:
                    unhealthy += 1
            
            return {
                "total_agents": len(self._agents),
                "healthy": healthy,
                "unhealthy": unhealthy,
                "pools": {
                    tid: len(pool) for tid, pool in self._pools.items()
                }
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        
        return {
            "spawned": self._spawn_count,
            "destroyed": self._destroy_count,
            "active": len(self._agents),
            "pools": len(self._pools),
            "pool_sizes": {
                tid: len(pool) for tid, pool in self._pools.items()
            }
        }
    
    async def shutdown(self):
        
        self._logger.info("Shutting down Agent Factory...")
        
        async with self._pool_lock:
            for pooled in list(self._agents.values()):
                try:
                    await pooled.agent.terminate()
                except Exception as e:
                    self._logger.error(f"Error terminating agent {pooled.agent.agent_id}: {e}")
            
            self._agents.clear()
            self._pools.clear()
        
        self._logger.info("Agent Factory shutdown complete")

_factory: Optional[AgentFactory] = None

async def get_agent_factory() -> AgentFactory:
    
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory

def reset_factory():
    
    global _factory
    _factory = None