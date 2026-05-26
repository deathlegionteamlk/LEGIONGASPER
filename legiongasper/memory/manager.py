from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

from .session import SessionMemory
from .working import WorkingMemory
from .daily import DailyMemory
from .long_term import LongTermMemory
from .collective import CollectiveConsciousness
from .base import MemoryEntry

class MemoryManager:
    
    def __init__(self, 
                 session_id: str,
                 task_id: str,
                 agent_id: str,
                 redis_url: Optional[str] = None,
                 chroma_path: str = "./data/chroma_db"):
        
        self.agent_id = agent_id
        self.session_id = session_id
        self.task_id = task_id
        
        self.session_memory = SessionMemory(session_id)
        self.working_memory = WorkingMemory(task_id)
        self.daily_memory = DailyMemory()
        self.long_term_memory = LongTermMemory(db_path=chroma_path)
        self.collective = CollectiveConsciousness()
        
        self.collective.set_long_term_reference(self.long_term_memory)
        
        self.layers = [
            self.session_memory,
            self.working_memory,
            self.daily_memory,
            self.long_term_memory,
            self.collective
        ]
    
    async def store(self, content: str, 
                   layer: Optional[str] = None,
                   importance: float = 1.0,
                   tags: List[str] = [],
                   **kwargs) -> str:
        
        metadata = {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            **kwargs
        }
        
        if layer is None:
            layer = self._auto_route_layer(importance, tags)
        
        if layer == "session":
            return await self.session_memory.store(content, importance=importance, tags=tags, **metadata)
        elif layer == "working":
            return await self.working_memory.store(content, importance=importance, tags=tags, **metadata)
        elif layer == "daily":
            return await self.daily_memory.store(content, importance=importance, tags=tags, **metadata)
        elif layer == "long_term":
            return await self.long_term_memory.store(content, importance=importance, tags=tags, **metadata)
        elif layer == "collective":
            return await self.collective.store(content, importance=importance, tags=tags, **metadata)
        else:
            raise ValueError(f"Unknown memory layer: {layer}")
    
    def _auto_route_layer(self, importance: float, tags: List[str]) -> str:
        
        if importance >= 0.8:
            return "collective"
        elif importance >= 0.6:
            return "long_term"
        elif importance >= 0.4:
            return "daily"
        elif importance >= 0.2:
            return "working"
        else:
            return "session"
    
    async def retrieve(self, query: str, 
                      layers: List[str] = None,
                      limit_per_layer: int = 5) -> Dict[str, List[MemoryEntry]]:
        
        if layers is None:
            layers = ["session", "working", "daily", "long_term", "collective"]
        
        results = {}
        
        for layer_name in layers:
            try:
                if layer_name == "session":
                    results[layer_name] = await self.session_memory.retrieve(query, limit_per_layer)
                elif layer_name == "working":
                    results[layer_name] = await self.working_memory.retrieve(query, limit_per_layer)
                elif layer_name == "daily":
                    results[layer_name] = await self.daily_memory.retrieve(query, limit_per_layer)
                elif layer_name == "long_term":
                    results[layer_name] = await self.long_term_memory.retrieve(query, limit_per_layer)
                elif layer_name == "collective":
                    results[layer_name] = await self.collective.retrieve(query, limit_per_layer)
            except Exception as e:
                results[layer_name] = []
        
        return results
    
    async def get_context(self, max_tokens: int = 4000) -> str:
        
        context_parts = []
        
        session_ctx = await self.session_memory.get_context_window(max_tokens // 2)
        if session_ctx:
            context_parts.append("## Current Session\n" + session_ctx)
        
        working_ctx = await self.working_memory.get_task_context()
        if working_ctx:
            context_parts.append(f"## Task Context\nTask: {working_ctx['task_id']}")
        
        daily_summary = await self.daily_memory.get_day_summary()
        if daily_summary:
            context_parts.append("## Today's Activity\n" + daily_summary[:500])
        
        collective_insights = await self.collective.get_collective_insights()
        if collective_insights["total_knowledge_items"] > 0:
            context_parts.append(
                f"## Collective Knowledge\n"
                f"Available knowledge: {collective_insights['total_knowledge_items']} items\n"
                f"Contributors: {collective_insights['active_contributors']}"
            )
        
        return "\n\n".join(context_parts)
    
    async def consolidate(self):
        
        session_entries = await self.session_memory.retrieve(limit=50)
        for entry in session_entries:
            if entry.importance >= 0.5:
                await self.working_memory.store(
                    entry.content,
                    importance=entry.importance,
                    tags=entry.tags
                )
        
        working_summary = await self.working_memory.consolidate()
        if working_summary:
            await self.daily_memory.store(
                working_summary,
                importance=0.6,
                tags=["consolidated", "working_summary"]
            )
        
        daily_entries = await self.daily_memory.retrieve(limit=20)
        for entry in daily_entries:
            if entry.importance >= 0.7:
                await self.long_term_memory.store(
                    entry.content,
                    importance=entry.importance,
                    tags=entry.tags
                )
    
    async def share_to_collective(self, content: str, tags: List[str] = []):
        
        await self.collective.store(
            content,
            agent_id=self.agent_id,
            importance=0.9,
            tags=["shared"] + tags
        )
    
    async def clear(self, layer: Optional[str] = None):
        
        if layer is None:
            
            for l in self.layers:
                await l.clear(self.agent_id)
        elif layer == "session":
            await self.session_memory.clear()
        elif layer == "working":
            await self.working_memory.clear(self.agent_id)
        elif layer == "daily":
            await self.daily_memory.clear(self.agent_id)
        elif layer == "long_term":
            await self.long_term_memory.clear(self.agent_id)
        elif layer == "collective":
            await self.collective.clear(self.agent_id)
    
    def get_stats(self) -> Dict[str, Any]:
        
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "layers": {
                layer.layer_name: layer.get_stats()
                for layer in self.layers
            }
        }