import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import inspect
import json

class ToolPermission(Enum):
    
    PUBLIC = "public"  
    RESTRICTED = "restricted"  
    ADMIN = "admin"  
    DISABLED = "disabled"  

@dataclass
class ToolParameter:
    
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None

@dataclass
class ToolSchema:
    
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: Dict[str, Any] = field(default_factory=dict)
    permission: ToolPermission = ToolPermission.PUBLIC
    timeout_seconds: int = 60
    rate_limit: Optional[int] = None  
    tags: List[str] = field(default_factory=list)

class ToolRegistry:
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, ToolSchema] = {}
        self._usage_stats: Dict[str, Dict[str, int]] = {}
        self._lock = asyncio.Lock()
    
    def register(self, 
                 schema: ToolSchema,
                 func: Callable,
                 override: bool = False):
        
        if schema.name in self._tools and not override:
            raise ValueError(f"Tool {schema.name} already registered")
        
        self._tools[schema.name] = func
        self._schemas[schema.name] = schema
        self._usage_stats[schema.name] = {"calls": 0, "errors": 0}
    
    def unregister(self, name: str):
        
        if name in self._tools:
            del self._tools[name]
            del self._schemas[name]
            del self._usage_stats[name]
    
    def get(self, name: str) -> Optional[Callable]:
        
        return self._tools.get(name)
    
    def get_schema(self, name: str) -> Optional[ToolSchema]:
        
        return self._schemas.get(name)
    
    def list_tools(self, 
                   permission: Optional[ToolPermission] = None,
                   tags: Optional[List[str]] = None) -> List[str]:
        
        tools = list(self._tools.keys())
        
        if permission:
            tools = [
                t for t in tools
                if self._schemas[t].permission == permission
            ]
        
        if tags:
            tools = [
                t for t in tools
                if any(tag in self._schemas[t].tags for tag in tags)
            ]
        
        return tools
    
    def get_all_schemas(self) -> Dict[str, ToolSchema]:
        
        return self._schemas.copy()
    
    async def execute(self, 
                     name: str,
                     agent_id: str,
                     **kwargs) -> Dict[str, Any]:
        
        async with self._lock:
            tool = self._tools.get(name)
            schema = self._schemas.get(name)
            
            if not tool or not schema:
                return {
                    "success": False,
                    "error": f"Tool not found: {name}"
                }
            
            if schema.permission == ToolPermission.DISABLED:
                return {
                    "success": False,
                    "error": f"Tool {name} is disabled"
                }
            
            validation = self._validate_params(schema, kwargs)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            try:
                if asyncio.iscoroutinefunction(tool):
                    result = await asyncio.wait_for(
                        tool(**kwargs),
                        timeout=schema.timeout_seconds
                    )
                else:
                    
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: tool(**kwargs)),
                        timeout=schema.timeout_seconds
                    )
                
                self._usage_stats[name]["calls"] += 1
                
                return {
                    "success": True,
                    "result": result,
                    "tool": name,
                    "agent_id": agent_id
                }
                
            except asyncio.TimeoutError:
                self._usage_stats[name]["errors"] += 1
                return {
                    "success": False,
                    "error": f"Tool {name} timed out after {schema.timeout_seconds}s"
                }
            except Exception as e:
                self._usage_stats[name]["errors"] += 1
                return {
                    "success": False,
                    "error": str(e),
                    "tool": name
                }
    
    def _validate_params(self, 
                        schema: ToolSchema,
                        kwargs: Dict) -> Dict[str, Any]:
        
        errors = []
        
        for param in schema.parameters:
            if param.required and param.name not in kwargs:
                errors.append(f"Missing required parameter: {param.name}")
            
            if param.name in kwargs:
                value = kwargs[param.name]
                if param.type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {param.name} must be a string")
                elif param.type == "integer" and not isinstance(value, int):
                    errors.append(f"Parameter {param.name} must be an integer")
                elif param.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Parameter {param.name} must be a number")
                elif param.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter {param.name} must be a boolean")
                elif param.type == "array" and not isinstance(value, list):
                    errors.append(f"Parameter {param.name} must be an array")
                elif param.type == "object" and not isinstance(value, dict):
                    errors.append(f"Parameter {param.name} must be an object")
                
                if param.enum and value not in param.enum:
                    errors.append(f"Parameter {param.name} must be one of: {param.enum}")
        
        if errors:
            return {"valid": False, "error": "; ".join(errors)}
        
        return {"valid": True}
    
    def get_openai_schema(self, name: str) -> Optional[Dict]:
        
        schema = self._schemas.get(name)
        if not schema:
            return None
        
        properties = {}
        required = []
        
        for param in schema.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": schema.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def get_all_openai_schemas(self) -> List[Dict]:
        
        return [
            self.get_openai_schema(name)
            for name in self._tools.keys()
            if self.get_openai_schema(name)
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        
        return {
            "total_tools": len(self._tools),
            "usage": self._usage_stats.copy()
        }

def create_schema_from_function(func: Callable, 
                                 name: Optional[str] = None,
                                 description: Optional[str] = None) -> ToolSchema:
    
    sig = inspect.signature(func)
    
    parameters = []
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'cls']:
            continue
        
        param_type = "string"
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list:
                param_type = "array"
            elif param.annotation == dict:
                param_type = "object"
        
        tool_param = ToolParameter(
            name=param_name,
            type=param_type,
            description=f"Parameter {param_name}",
            required=param.default == inspect.Parameter.empty,
            default=param.default if param.default != inspect.Parameter.empty else None
        )
        parameters.append(tool_param)
    
    return ToolSchema(
        name=name or func.__name__,
        description=description or func.__doc__ or f"Tool {func.__name__}",
        parameters=parameters
    )