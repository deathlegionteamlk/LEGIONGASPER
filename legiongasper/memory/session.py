from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
from .base import BaseMemory, MemoryEntry

class SessionMemory(BaseMemory):
    
    def __init__(self, session_id: str, max_entries: int = 100, ttl_seconds: int = 3600):
        super().__init__("session", max_entries)
        self.session_id = session_id
        self.ttl_seconds = ttl_seconds
        self._entries: deque = deque(maxlen=max_entries)
        self._created_at = datetime.utcnow()
    
    async def store(self, content: str, **kwargs) -> str:
        
        entry = self.create_entry(
            content=content,
            session_id=self.session_id,
            **kwargs
        )
        self._entries.append(entry)
        return entry.id
    
    async def retrieve(self, query: str = "", limit: int = 10) -> List[MemoryEntry]:
        
        cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
        valid_entries = [
            e for e in self._entries 
            if e.timestamp > cutoff
        ]
        
        return list(valid_entries)[-limit:]
    
    async def get_context_window(self, max_tokens: int = 4000) -> str:
        
        entries = await self.retrieve(limit=50)
        
        context_parts = []
        current_tokens = 0
        
        for entry in reversed(entries):
            
            entry_tokens = len(entry.content.split())
            if current_tokens + entry_tokens > max_tokens:
                break
            context_parts.append(f"[{entry.timestamp.isoformat()}] {entry.content}")
            current_tokens += entry_tokens
        
        return "\n".join(reversed(context_parts))
    
    async def clear(self, agent_id: Optional[str] = None):
        
        self._entries.clear()
    
    def is_expired(self) -> bool:
        
        age = datetime.utcnow() - self._created_at
        return age.total_seconds() > self.ttl_seconds
    
    def get_stats(self) -> Dict[str, Any]:
        
        stats = super().get_stats()
        stats.update({
            "session_id": self.session_id,
            "created_at": self._created_at.isoformat(),
            "is_expired": self.is_expired(),
            "ttl_seconds": self.ttl_seconds
        })
        return stats