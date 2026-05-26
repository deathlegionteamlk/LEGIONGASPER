import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class AuditEvent:
    
    event_id: str
    event_type: str  
    actor_id: str  
    actor_type: str  
    action: str
    resource: str
    status: str  
    details: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }

class AuditLogger:
    
    def __init__(self, 
                 log_dir: str = "./data/audit",
                 batch_size: int = 100,
                 flush_interval: int = 60):
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
        self._logger = logging.getLogger(__name__)
    
    async def start(self):
        
        self._flush_task = asyncio.create_task(self._flush_loop())
    
    async def stop(self):
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        await self._flush_buffer()
    
    async def log(self,
                 event_type: str,
                 actor_id: str,
                 actor_type: str,
                 action: str,
                 resource: str,
                 status: str = "success",
                 details: Dict[str, Any] = None,
                 session_id: Optional[str] = None,
                 ip_address: Optional[str] = None):
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            resource=resource,
            status=status,
            details=details or {},
            timestamp=datetime.utcnow(),
            session_id=session_id,
            ip_address=ip_address
        )
        
        async with self._buffer_lock:
            self._buffer.append(event)
            
            if len(self._buffer) >= self.batch_size:
                await self._flush_buffer()
    
    async def log_agent_spawn(self, 
                             agent_id: str,
                             template_id: str,
                             session_id: str,
                             status: str = "success"):
        
        await self.log(
            event_type="agent_spawn",
            actor_id="system",
            actor_type="system",
            action="spawn",
            resource=f"agent:{agent_id}",
            status=status,
            details={"template_id": template_id},
            session_id=session_id
        )
    
    async def log_task_execution(self,
                                agent_id: str,
                                task_id: str,
                                task_description: str,
                                status: str = "success",
                                duration_ms: Optional[float] = None):
        
        await self.log(
            event_type="task_execute",
            actor_id=agent_id,
            actor_type="agent",
            action="execute",
            resource=f"task:{task_id}",
            status=status,
            details={
                "description": task_description[:100],
                "duration_ms": duration_ms
            }
        )
    
    async def log_tool_call(self,
                           agent_id: str,
                           tool_name: str,
                           status: str = "success",
                           error: Optional[str] = None):
        
        await self.log(
            event_type="tool_call",
            actor_id=agent_id,
            actor_type="agent",
            action="call",
            resource=f"tool:{tool_name}",
            status=status,
            details={"error": error} if error else {}
        )
    
    async def log_llm_request(self,
                             agent_id: str,
                             provider: str,
                             model: str,
                             tokens_in: int,
                             tokens_out: int,
                             cost: float,
                             status: str = "success"):
        
        await self.log(
            event_type="llm_request",
            actor_id=agent_id,
            actor_type="agent",
            action="request",
            resource=f"llm:{provider}:{model}",
            status=status,
            details={
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost": cost
            }
        )
    
    async def query(self,
                   actor_id: Optional[str] = None,
                   event_type: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[AuditEvent]:
        
        events = []
        
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        data = json.loads(line)
                        event_time = datetime.fromisoformat(data['timestamp'])
                        
                        if start_time and event_time < start_time:
                            continue
                        if end_time and event_time > end_time:
                            continue
                        if actor_id and data.get('actor_id') != actor_id:
                            continue
                        if event_type and data.get('event_type') != event_type:
                            continue
                        
                        events.append(AuditEvent(**data))
                        
                        if len(events) >= limit:
                            break
            except Exception as e:
                self._logger.error(f"Error reading {log_file}: {e}")
        
        return events[:limit]
    
    async def _flush_loop(self):
        
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        
        async with self._buffer_lock:
            if not self._buffer:
                return
            
            today = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"audit_{today}.jsonl"
            
            try:
                with open(log_file, 'a') as f:
                    for event in self._buffer:
                        f.write(json.dumps(event.to_dict()) + '\n')
                
                self._logger.debug(f"Flushed {len(self._buffer)} audit events")
                self._buffer.clear()
            except Exception as e:
                self._logger.error(f"Failed to flush audit log: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        
        return {
            "buffer_size": len(self._buffer),
            "log_dir": str(self.log_dir),
            "batch_size": self.batch_size
        }

_audit_logger: Optional[AuditLogger] = None

async def get_audit_logger() -> AuditLogger:
    
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
        await _audit_logger.start()
    return _audit_logger