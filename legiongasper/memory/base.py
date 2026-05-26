from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

class MemoryEntry(BaseModel):
    
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    importance: float = 1.0  
    tags: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseMemory(ABC):
    
    def __init__(self, layer_name: str, max_entries: int = 1000):
        self.layer_name = layer_name
        self.max_entries = max_entries
        self._entries: Dict[str, MemoryEntry] = {}
    
    @abstractmethod
    async def store(self, content: str, **kwargs) -> str:
        
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        
        pass
    
    @abstractmethod
    async def clear(self, agent_id: Optional[str] = None):
        
        pass
    
    def create_entry(self, content: str, **kwargs) -> MemoryEntry:
        
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        return entry
    
    def get_stats(self) -> Dict[str, Any]:
        
        return {
            "layer": self.layer_name,
            "total_entries": len(self._entries),
            "max_entries": self.max_entries,
            "usage_percent": len(self._entries) / self.max_entries * 100
        }