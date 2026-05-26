import asyncio
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, field
import json

from ..config import AgentTemplate, get_settings
from ..memory import MemoryManager

class AgentState(Enum):
    
    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"

@dataclass
class AgentEvent:
    
    event_type: str  
    content: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps({
            "event_type": self.event_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        })

class ToolRegistry:
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict] = {}
    
    def register(self, name: str, func: Callable, schema: Optional[Dict] = None):
        
        self._tools[name] = func
        self._schemas[name] = schema or {}
    
    def get(self, name: str) -> Optional[Callable]:
        
        return self._tools.get(name)
    
    def get_schema(self, name: str) -> Optional[Dict]:
        
        return self._schemas.get(name)
    
    def list_tools(self) -> List[str]:
        
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> Dict[str, Dict]:
        
        return self._schemas.copy()
    
    async def execute(self, name: str, **kwargs) -> Any:
        
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        else:
            return tool(**kwargs)

class Agent:
    
    def __init__(self, 
                 template: AgentTemplate,
                 agent_id: Optional[str] = None,
                 session_id: Optional[str] = None):
        
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.template = template
        
        self.state = AgentState.IDLE
        self._state_lock = asyncio.Lock()
        
        self.tools = ToolRegistry()
        self.memory: Optional[MemoryManager] = None
        
        self._current_task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        self._created_at = datetime.utcnow()
        self._task_count = 0
        self._error_count = 0
        
        self._context: Dict[str, Any] = {}
    
    async def initialize(self):
        
        async with self._state_lock:
            self.state = AgentState.INITIALIZING
            
            self.memory = MemoryManager(
                session_id=self.session_id,
                task_id=f"task_{self.agent_id}",
                agent_id=self.agent_id
            )
            
            await self._register_template_tools()
            
            self.state = AgentState.READY
    
    async def _register_template_tools(self):
        
        pass
    
    async def execute(self, task: str, 
                     context: Optional[Dict] = None,
                     stream: bool = False) -> Any:
        
        if stream:
            return self._execute_streaming(task, context)
        else:
            return await self._execute_sync(task, context)
    
    async def _execute_sync(self, task: str, context: Optional[Dict]) -> Dict[str, Any]:
        
        async with self._state_lock:
            if self.state not in [AgentState.READY, AgentState.IDLE]:
                raise RuntimeError(f"Agent not ready: {self.state}")
            self.state = AgentState.EXECUTING
        
        try:
            self._task_count += 1
            
            await self._emit_event("thought", f"Analyzing task: {task[:100]}...")
            
            full_context = await self._build_context(task, context)
            
            result = await self._process_with_llm(task, full_context)
            
            if self.memory:
                await self.memory.store(
                    f"Task: {task}\nResult: {result}",
                    importance=0.7,
                    tags=["execution", "result"]
                )
            
            await self._emit_event("result", result)
            
            async with self._state_lock:
                self.state = AgentState.READY
            
            return {
                "success": True,
                "result": result,
                "agent_id": self.agent_id,
                "task": task
            }
            
        except Exception as e:
            self._error_count += 1
            await self._emit_event("error", str(e))
            
            async with self._state_lock:
                self.state = AgentState.ERROR
            
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
                "task": task
            }
    
    async def _execute_streaming(self, task: str, 
                                  context: Optional[Dict]) -> AsyncGenerator[AgentEvent, None]:
        
        execution_task = asyncio.create_task(
            self._execute_sync(task, context)
        )
        
        while not execution_task.done():
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=0.1
                )
                yield event
            except asyncio.TimeoutError:
                continue
        
        result = await execution_task
        yield AgentEvent(
            event_type="complete",
            content=result
        )
    
    async def _emit_event(self, event_type: str, content: Any, metadata: Dict = None):
        
        event = AgentEvent(
            event_type=event_type,
            content=content,
            metadata=metadata or {}
        )
        await self._event_queue.put(event)
    
    async def _build_context(self, task: str, context: Optional[Dict]) -> str:
        
        parts = []
        
        if self.template.system_prompt:
            parts.append(f"System: {self.template.system_prompt}")
        
        if self.memory:
            mem_context = await self.memory.get_context()
            if mem_context:
                parts.append(f"Context:\n{mem_context}")
        
        if context:
            parts.append(f"Additional Context: {json.dumps(context)}")
        
        parts.append(f"Task: {task}")
        
        return "\n\n".join(parts)
    
    async def _process_with_llm(self, task: str, context: str) -> str:
        
        await self._emit_event("action", "Processing with LLM")
        return f"Processed: {task[:50]}..."
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        
        await self._emit_event("action", f"Using tool: {tool_name}", {"params": kwargs})
        
        result = await self.tools.execute(tool_name, **kwargs)
        
        await self._emit_event("observation", result, {"tool": tool_name})
        
        return result
    
    async def pause(self):
        
        async with self._state_lock:
            if self.state == AgentState.EXECUTING:
                self.state = AgentState.PAUSED
    
    async def resume(self):
        
        async with self._state_lock:
            if self.state == AgentState.PAUSED:
                self.state = AgentState.EXECUTING
    
    async def terminate(self):
        
        async with self._state_lock:
            self.state = AgentState.TERMINATED
        
        if self._current_task:
            self._current_task.cancel()
    
    def get_state(self) -> AgentState:
        
        return self.state
    
    def get_info(self) -> Dict[str, Any]:
        
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "template_id": self.template.template_id,
            "role": self.template.role,
            "state": self.state.value,
            "created_at": self._created_at.isoformat(),
            "task_count": self._task_count,
            "error_count": self._error_count,
            "tools": self.tools.list_tools()
        }
    
    async def store_memory(self, content: str, importance: float = 0.5, tags: List[str] = None):
        
        if self.memory:
            await self.memory.store(content, importance=importance, tags=tags or [])