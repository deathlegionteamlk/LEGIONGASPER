import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import OrderedDict
from .base import BaseMemory, MemoryEntry

class WorkingMemory(BaseMemory):
    
    def __init__(self, task_id: str, max_entries: int = 500, ttl_seconds: int = 7200):
        super().__init__("working", max_entries)
        self.task_id = task_id
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def store(self, content: str, **kwargs) -> str:
        
        async with self._lock:
            entry = self.create_entry(
                content=content,
                **kwargs
            )
            
            while len(self._entries) >= self.max_entries:
                self._entries.popitem(last=False)
            
            self._entries[entry.id] = entry
            self._entries.move_to_end(entry.id)
            
            return entry.id
    
    async def retrieve(self, query: str = "", limit: int = 10) -> List[MemoryEntry]:
        
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=self.ttl_seconds)
            
            valid_entries = [
                e for e in self._entries.values()
                if e.timestamp > cutoff
            ]
            
            valid_entries.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            
            return valid_entries[:limit]
    
    async def get_task_context(self) -> Dict[str, Any]:
        
        entries = await self.retrieve(limit=20)
        
        return {
            "task_id": self.task_id,
            "entry_count": len(self._entries),
            "recent_entries": [
                {
                    "content": e.content[:200],
                    "timestamp": e.timestamp.isoformat(),
                    "importance": e.importance
                }
                for e in entries
            ]
        }
    
    async def update_importance(self, entry_id: str, importance: float):
        
        async with self._lock:
            if entry_id in self._entries:
                entry = self._entries[entry_id]
                entry.importance = max(0.0, min(1.0, importance))
    
    async def clear(self, agent_id: Optional[str] = None):
        
        async with self._lock:
            if agent_id:
                
                to_remove = [
                    k for k, v in self._entries.items()
                    if v.agent_id == agent_id
                ]
                for k in to_remove:
                    del self._entries[k]
            else:
                self._entries.clear()
    
    async def consolidate(self) -> str:
        
        entries = await self.retrieve(limit=100)
        
        if not entries:
            return ""
        
        by_tags: Dict[str, List[str]] = {}
        for entry in entries:
            for tag in entry.tags:
                if tag not in by_tags:
                    by_tags[tag] = []
                by_tags[tag].append(entry.content)
        
        summary_parts = []
        for tag, contents in by_tags.items():
            summary_parts.append(f"[{tag}]: {len(contents)} items")
        
        return "\n".join(summary_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        
        stats = super().get_stats()
        stats.update({
            "task_id": self.task_id,
            "ttl_seconds": self.ttl_seconds
        })
        return stats