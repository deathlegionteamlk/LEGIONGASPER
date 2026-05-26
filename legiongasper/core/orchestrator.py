import asyncio
import uuid
import heapq
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

from .agent import Agent
from .captain import Captain
from .factory import get_agent_factory

class TaskPriority(Enum):
    
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4

class TaskStatus(Enum):
    
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class TaskDependency:
    
    task_id: str
    required_status: TaskStatus = TaskStatus.COMPLETED

@dataclass
class OrchestratorTask:
    
    task_id: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    
    assigned_agent_id: Optional[str] = None
    captain_id: Optional[str] = None
    
    dependencies: List[TaskDependency] = field(default_factory=list)
    
    context: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 300
    
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    
    def __lt__(self, other):
        
        if not isinstance(other, OrchestratorTask):
            return NotImplemented
        return (self.priority.value, self.created_at) < (other.priority.value, other.created_at)

@dataclass
class TaskQueueStats:
    
    pending: int = 0
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    total: int = 0

class Orchestrator:
    
    def __init__(self, 
                 max_concurrent: int = 10,
                 poll_interval: float = 1.0):
        
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        
        self._tasks: Dict[str, OrchestratorTask] = {}
        self._priority_queue: List[tuple] = []  
        self._queue_lock = asyncio.Lock()
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
        
        self._status_callbacks: Dict[TaskStatus, List[Callable]] = {}
        
        self._started = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        self._logger = logging.getLogger(__name__)
    
    async def start(self):
        
        if self._started:
            return
        
        self._logger.info("Starting Task Orchestrator")
        self._started = True
        self._shutdown_event.clear()
        
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        
        if not self._started:
            return
        
        self._logger.info("Stopping Task Orchestrator")
        self._shutdown_event.set()
        
        for task in self._running_tasks.values():
            task.cancel()
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        self._started = False
    
    async def submit(self,
                    description: str,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    dependencies: List[str] = None,
                    context: Dict[str, Any] = None,
                    timeout_seconds: int = 300,
                    tags: List[str] = None) -> str:
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task_deps = []
        if dependencies:
            for dep_id in dependencies:
                task_deps.append(TaskDependency(task_id=dep_id))
        
        task = OrchestratorTask(
            task_id=task_id,
            description=description,
            priority=priority,
            dependencies=task_deps,
            context=context or {},
            timeout_seconds=timeout_seconds,
            tags=tags or []
        )
        
        async with self._queue_lock:
            self._tasks[task_id] = task
            
            if await self._check_dependencies(task):
                task.status = TaskStatus.QUEUED
                heapq.heappush(self._priority_queue, (task.priority.value, task_id))
                self._logger.info(f"Task {task_id} queued with priority {priority.name}")
            else:
                task.status = TaskStatus.PENDING
                self._logger.info(f"Task {task_id} pending (waiting for dependencies)")
        
        return task_id
    
    async def submit_to_captain(self,
                                captain: Captain,
                                description: str,
                                priority: TaskPriority = TaskPriority.NORMAL,
                                context: Dict[str, Any] = None) -> str:
        
        task_id = await self.submit(
            description=description,
            priority=priority,
            context=context
        )
        
        async with self._queue_lock:
            self._tasks[task_id].captain_id = captain.captain_id
        
        return task_id
    
    async def cancel(self, task_id: str) -> bool:
        
        async with self._queue_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False
            
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            
            self._logger.info(f"Task {task_id} cancelled")
            return True
    
    async def get_task(self, task_id: str) -> Optional[OrchestratorTask]:
        
        return self._tasks.get(task_id)
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        
        start_time = datetime.utcnow()
        
        while True:
            task = await self.get_task(task_id)
            if not task:
                return None
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            
            if task.status == TaskStatus.FAILED:
                raise Exception(task.error or "Task failed")
            
            if timeout:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > timeout:
                    raise TimeoutError(f"Timeout waiting for task {task_id}")
            
            await asyncio.sleep(0.1)
    
    async def list_tasks(self, 
                        status: Optional[TaskStatus] = None,
                        tags: Optional[List[str]] = None) -> List[OrchestratorTask]:
        
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return tasks
    
    async def get_stats(self) -> TaskQueueStats:
        
        stats = TaskQueueStats()
        
        for task in self._tasks.values():
            stats.total += 1
            if task.status == TaskStatus.PENDING:
                stats.pending += 1
            elif task.status == TaskStatus.QUEUED:
                stats.queued += 1
            elif task.status == TaskStatus.RUNNING:
                stats.running += 1
            elif task.status == TaskStatus.COMPLETED:
                stats.completed += 1
            elif task.status == TaskStatus.FAILED:
                stats.failed += 1
        
        return stats
    
    async def _scheduler_loop(self):
        
        while not self._shutdown_event.is_set():
            try:
                
                await self._process_queue()
                
                await self._check_pending_tasks()
                
                await self._cleanup_tasks()
                
            except Exception as e:
                self._logger.error(f"Scheduler error: {e}")
            
            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=self.poll_interval
            )
    
    async def _process_queue(self):
        
        async with self._queue_lock:
            while self._priority_queue and len(self._running_tasks) < self.max_concurrent:
                
                _, task_id = heapq.heappop(self._priority_queue)
                
                task = self._tasks.get(task_id)
                if not task or task.status != TaskStatus.QUEUED:
                    continue
                
                execution_task = asyncio.create_task(
                    self._execute_task(task_id)
                )
                self._running_tasks[task_id] = execution_task
    
    async def _execute_task(self, task_id: str):
        
        task = self._tasks.get(task_id)
        if not task:
            return
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        self._logger.info(f"Executing task {task_id}")
        
        try:
            
            result = await asyncio.wait_for(
                self._run_task(task),
                timeout=task.timeout_seconds
            )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            self._logger.info(f"Task {task_id} completed successfully")
            await self._notify_status_change(task)
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = "Task timed out"
            task.completed_at = datetime.utcnow()
            
            self._logger.warning(f"Task {task_id} timed out")
            await self._handle_failure(task)
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            
            self._logger.error(f"Task {task_id} failed: {e}")
            await self._handle_failure(task)
        
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    async def _run_task(self, task: OrchestratorTask) -> Any:
        
        if task.captain_id:
            
            return {"status": "completed", "method": "captain"}
        
        factory = await get_agent_factory()
        
        agent = await factory.spawn("researcher")
        
        try:
            
            result = await agent.execute(task.description, task.context)
            return result
        finally:
            
            await factory.release(agent.agent_id)
    
    async def _handle_failure(self, task: OrchestratorTask):
        
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.QUEUED
            task.error = None
            
            async with self._queue_lock:
                heapq.heappush(self._priority_queue, (task.priority.value, task.task_id))
            
            self._logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
        else:
            await self._notify_status_change(task)
    
    async def _check_dependencies(self, task: OrchestratorTask) -> bool:
        
        for dep in task.dependencies:
            dep_task = self._tasks.get(dep.task_id)
            if not dep_task:
                return False
            if dep_task.status != dep.required_status:
                return False
        return True
    
    async def _check_pending_tasks(self):
        
        async with self._queue_lock:
            for task in self._tasks.values():
                if task.status == TaskStatus.PENDING:
                    if await self._check_dependencies(task):
                        task.status = TaskStatus.QUEUED
                        heapq.heappush(self._priority_queue, (task.priority.value, task.task_id))
    
    async def _cleanup_tasks(self):
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        async with self._queue_lock:
            to_remove = [
                task_id for task_id, task in self._tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at and task.completed_at < cutoff
            ]
            
            for task_id in to_remove:
                del self._tasks[task_id]
    
    def on_status_change(self, status: TaskStatus, callback: Callable):
        
        if status not in self._status_callbacks:
            self._status_callbacks[status] = []
        self._status_callbacks[status].append(callback)
    
    async def _notify_status_change(self, task: OrchestratorTask):
        
        callbacks = self._status_callbacks.get(task.status, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                self._logger.error(f"Status callback error: {e}")

_orchestrator: Optional[Orchestrator] = None

async def get_orchestrator() -> Orchestrator:
    
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
        await _orchestrator.start()
    return _orchestrator