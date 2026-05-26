import asyncio
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from .base import BaseMemory, MemoryEntry

class CollectiveConsciousness(BaseMemory):
    
    def __init__(self, max_entries: int = 50000):
        super().__init__("collective", max_entries)
        self._knowledge_patterns: Dict[str, Dict[str, Any]] = {}
        self._agent_contributions: Dict[str, int] = {}
        self._shared_insights: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._long_term_ref = None  
    
    def set_long_term_reference(self, long_term_memory):
        
        self._long_term_ref = long_term_memory
    
    async def store(self, content: str, **kwargs) -> str:
        
        entry = self.create_entry(content=content, **kwargs)
        
        async with self._lock:
            self._entries[entry.id] = entry
            
            agent_id = kwargs.get('agent_id')
            if agent_id:
                self._agent_contributions[agent_id] = self._agent_contributions.get(agent_id, 0) + 1
            
            await self._extract_patterns(entry)
            
            if self._long_term_ref:
                await self._long_term_ref.store(content, **kwargs)
            
            return entry.id
    
    async def _extract_patterns(self, entry: MemoryEntry):
        
        for tag in entry.tags:
            if tag not in self._knowledge_patterns:
                self._knowledge_patterns[tag] = {
                    "count": 0,
                    "first_seen": entry.timestamp.isoformat(),
                    "last_seen": entry.timestamp.isoformat(),
                    "entries": []
                }
            
            pattern = self._knowledge_patterns[tag]
            pattern["count"] += 1
            pattern["last_seen"] = entry.timestamp.isoformat()
            pattern["entries"].append(entry.id)
            
            if len(pattern["entries"]) > 100:
                pattern["entries"] = pattern["entries"][-100:]
    
    async def retrieve(self, query: str = "", limit: int = 10) -> List[MemoryEntry]:
        
        async with self._lock:
            
            entries = sorted(
                self._entries.values(),
                key=lambda x: (x.importance, x.timestamp),
                reverse=True
            )
            
            if query:
                entries = [
                    e for e in entries
                    if query.lower() in e.content.lower() or query in e.tags
                ]
            
            return entries[:limit]
    
    async def get_collective_insights(self, topic: Optional[str] = None) -> Dict[str, Any]:
        
        async with self._lock:
            insights = {
                "total_knowledge_items": len(self._entries),
                "active_contributors": len(self._agent_contributions),
                "top_contributors": sorted(
                    self._agent_contributions.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                "top_patterns": sorted(
                    [
                        {"tag": k, "count": v["count"], "last_seen": v["last_seen"]}
                        for k, v in self._knowledge_patterns.items()
                    ],
                    key=lambda x: x["count"],
                    reverse=True
                )[:10]
            }
            
            if topic:
                topic_entries = [
                    e for e in self._entries.values()
                    if topic.lower() in e.content.lower() or topic in e.tags
                ]
                insights["topic_count"] = len(topic_entries)
                insights["topic_relevance"] = len(topic_entries) / max(len(self._entries), 1)
            
            return insights
    
    async def share_knowledge(self, source_agent: str, target_agents: List[str], 
                             knowledge_filter: Optional[str] = None) -> List[str]:
        
        async with self._lock:
            
            shared_ids = []
            
            for entry_id, entry in self._entries.items():
                if entry.agent_id == source_agent:
                    if knowledge_filter is None or knowledge_filter in entry.tags:
                        
                        if "shared_with" not in entry.metadata:
                            entry.metadata["shared_with"] = []
                        entry.metadata["shared_with"].extend(target_agents)
                        shared_ids.append(entry_id)
            
            return shared_ids
    
    async def synthesize_knowledge(self, tags: List[str]) -> str:
        
        async with self._lock:
            
            relevant = [
                e for e in self._entries.values()
                if any(t in e.tags for t in tags)
            ]
            
            if not relevant:
                return "No relevant knowledge found."
            
            by_time: Dict[str, List[str]] = {}
            for entry in relevant:
                period = entry.timestamp.strftime("%Y-%m")
                if period not in by_time:
                    by_time[period] = []
                by_time[period].append(entry.content[:200])
            
            synthesis_parts = [f"Knowledge synthesis for tags: {', '.join(tags)}"]
            for period, contents in sorted(by_time.items()):
                synthesis_parts.append(f"\n[{period}]: {len(contents)} contributions")
            
            return "\n".join(synthesis_parts)
    
    async def get_emerging_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            recent_patterns = {}
            for tag, pattern in self._knowledge_patterns.items():
                last_seen = datetime.fromisoformat(pattern["last_seen"])
                if last_seen > cutoff:
                    recent_patterns[tag] = pattern["count"]
            
            trends = [
                {"tag": tag, "frequency": count}
                for tag, count in sorted(
                    recent_patterns.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ][:10]
            
            return trends
    
    async def clear(self, agent_id: Optional[str] = None):
        
        async with self._lock:
            if agent_id:
                
                to_remove = [
                    k for k, v in self._entries.items()
                    if v.agent_id == agent_id
                ]
                for k in to_remove:
                    del self._entries[k]
                
                if agent_id in self._agent_contributions:
                    del self._agent_contributions[agent_id]
            else:
                self._entries.clear()
                self._knowledge_patterns.clear()
                self._agent_contributions.clear()
                self._shared_insights.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        
        stats = super().get_stats()
        stats.update({
            "knowledge_patterns": len(self._knowledge_patterns),
            "contributing_agents": len(self._agent_contributions),
            "shared_insights": len(self._shared_insights)
        })
        return stats