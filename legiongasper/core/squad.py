import asyncio
import uuid
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import logging

from .agent import Agent
from .factory import get_agent_factory, AgentFactory

@dataclass
class SquadTask:
    
    task_id: str
    description: str
    assigned_agent_id: Optional[str] = None
    status: str = "pending"  
    result: Any = None
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class SquadResult:
    
    squad_id: str
    task_results: Dict[str, Any]
    completed_count: int
    failed_count: int
    total_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class Squad:
    
    def __init__(self,
                 captain_id: Optional[str] = None,
                 template_ids: List[str] = None,
                 squad_id: Optional[str] = None,
                 max_parallel: int = 5):
        
        self.squad_id = squad_id or f"squad_{uuid.uuid4().hex[:8]}"
        self.captain_id = captain_id
        self.template_ids = template_ids or []
        self.max_parallel = max_parallel
        
        self.agents: Dict[str, Agent] = {}
        self.agent_status: Dict[str, str] = {}  
        
        self._semaphore = asyncio.Semaphore(max_parallel)
        self._execution_lock = asyncio.Lock()
        
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._completed_tasks: List[SquadTask] = []
        
        self._message_bus: asyncio.Queue = asyncio.Queue()
        self._subscribers: Dict[str, List[Callable]] = {}
        
        self._initialized = False
        self._running = False
        
        self._logger = logging.getLogger(f"{__name__}.{self.squad_id}")
    
    async def initialize(self):
        
        if self._initialized:
            return
        
        self._logger.info(f"Initializing squad {self.squad_id}")
        
        factory = await get_agent_factory()
        
        for template_id in self.template_ids:
            try:
                agent = await factory.spawn(
                    template_id=template_id,
                    session_id=f"squad_{self.squad_id}"
                )
                self.agents[agent.agent_id] = agent
                self.agent_status[agent.agent_id] = "idle"
                self._logger.info(f"Added agent {agent.agent_id} to squad")
            except Exception as e:
                self._logger.error(f"Failed to spawn agent from {template_id}: {e}")
        
        if not self.agents:
            raise RuntimeError("Failed to initialize squad: no agents spawned")
        
        self._initialized = True
        self._logger.info(f"Squad {self.squad_id} initialized with {len(self.agents)} agents")
    
    async def execute_parallel(self, 
                              tasks: List[str],
                              context: Optional[Dict] = None) -> SquadResult:
        
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        
        squad_tasks = [
            SquadTask(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                description=task
            )
            for task in tasks
        ]
        
        self._logger.info(f"Executing {len(squad_tasks)} tasks in parallel")
        
        execution_tasks = [
            self._execute_with_semaphore(st, context)
            for st in squad_tasks
        ]
        
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        task_results = {}
        completed = 0
        failed = 0
        
        for squad_task, result in zip(squad_tasks, results):
            if isinstance(result, Exception):
                squad_task.status = "failed"
                squad_task.result = {"error": str(result)}
                failed += 1
            else:
                squad_task.status = "completed"
                squad_task.result = result
                completed += 1
            
            squad_task.completed_at = datetime.utcnow()
            task_results[squad_task.task_id] = {
                "description": squad_task.description,
                "status": squad_task.status,
                "result": squad_task.result
            }
            
            self._completed_tasks.append(squad_task)
        
        end_time = datetime.utcnow()
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return SquadResult(
            squad_id=self.squad_id,
            task_results=task_results,
            completed_count=completed,
            failed_count=failed,
            total_time_ms=total_time_ms,
            metadata={
                "agent_count": len(self.agents),
                "max_parallel": self.max_parallel
            }
        )
    
    async def _execute_with_semaphore(self, 
                                     squad_task: SquadTask,
                                     context: Optional[Dict]) -> Any:
        
        async with self._semaphore:
            
            agent = await self._acquire_agent()
            if not agent:
                raise RuntimeError("No available agents")
            
            squad_task.assigned_agent_id = agent.agent_id
            squad_task.status = "running"
            squad_task.started_at = datetime.utcnow()
            
            try:
                
                await self._broadcast("task_started", {
                    "squad_id": self.squad_id,
                    "task_id": squad_task.task_id,
                    "agent_id": agent.agent_id
                })
                
                result = await agent.execute(squad_task.description, context)
                
                await self._broadcast("task_completed", {
                    "squad_id": self.squad_id,
                    "task_id": squad_task.task_id,
                    "agent_id": agent.agent_id,
                    "success": result.get("success", False)
                })
                
                return result
                
            finally:
                await self._release_agent(agent.agent_id)
    
    async def _acquire_agent(self) -> Optional[Agent]:
        
        async with self._execution_lock:
            for agent_id, status in self.agent_status.items():
                if status == "idle":
                    self.agent_status[agent_id] = "busy"
                    return self.agents[agent_id]
        
        for _ in range(30):  
            await asyncio.sleep(1)
            async with self._execution_lock:
                for agent_id, status in self.agent_status.items():
                    if status == "idle":
                        self.agent_status[agent_id] = "busy"
                        return self.agents[agent_id]
        
        return None
    
    async def _release_agent(self, agent_id: str):
        
        async with self._execution_lock:
            if agent_id in self.agent_status:
                self.agent_status[agent_id] = "idle"
    
    async def get_available_agent(self) -> Optional[Agent]:
        
        async with self._execution_lock:
            for agent_id, status in self.agent_status.items():
                if status == "idle":
                    self.agent_status[agent_id] = "busy"
                    return self.agents[agent_id]
        return None
    
    async def release_agent(self, agent_id: str):
        
        await self._release_agent(agent_id)
    
    async def send_message(self, 
                          from_agent_id: str,
                          to_agent_id: str,
                          message: Any):
        
        msg = {
            "from": from_agent_id,
            "to": to_agent_id,
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._message_bus.put(msg)
        
        if to_agent_id in self._subscribers:
            for callback in self._subscribers[to_agent_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(msg)
                    else:
                        callback(msg)
                except Exception as e:
                    self._logger.error(f"Message callback error: {e}")
    
    async def broadcast(self, from_agent_id: str, message: Any):
        
        await self.send_message(from_agent_id, "broadcast", message)
    
    async def _broadcast(self, event_type: str, data: Dict):
        
        await self._message_bus.put({
            "type": event_type,
            "data": data
        })
    
    def subscribe(self, agent_id: str, callback: Callable):
        
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(callback)
    
    async def get_messages(self, 
                          agent_id: str,
                          timeout: float = 0.1) -> List[Dict]:
        
        messages = []
        
        try:
            while True:
                msg = await asyncio.wait_for(
                    self._message_bus.get(),
                    timeout=timeout
                )
                
                if msg.get("to") == agent_id or msg.get("to") == "broadcast":
                    messages.append(msg)
                elif msg.get("type"):  
                    messages.append(msg)
                    
        except asyncio.TimeoutError:
            pass
        
        return messages
    
    async def share_context(self, 
                           source_agent_id: str,
                           context_data: Any,
                           target_agent_ids: Optional[List[str]] = None):
        
        targets = target_agent_ids or list(self.agents.keys())
        
        for target_id in targets:
            if target_id != source_agent_id:
                await self.send_message(
                    source_agent_id,
                    target_id,
                    {
                        "type": "context_share",
                        "data": context_data
                    }
                )
    
    def get_status(self) -> Dict[str, Any]:
        
        return {
            "squad_id": self.squad_id,
            "captain_id": self.captain_id,
            "agent_count": len(self.agents),
            "agent_status": self.agent_status.copy(),
            "completed_tasks": len(self._completed_tasks),
            "max_parallel": self.max_parallel,
            "initialized": self._initialized
        }
    
    async def terminate(self):
        
        self._logger.info(f"Terminating squad {self.squad_id}")
        
        factory = await get_agent_factory()
        
        for agent_id in list(self.agents.keys()):
            try:
                await factory.destroy(agent_id)
            except Exception as e:
                self._logger.error(f"Error destroying agent {agent_id}: {e}")
        
        self.agents.clear()
        self.agent_status.clear()
        self._initialized = False
        
        self._logger.info(f"Squad {self.squad_id} terminated")