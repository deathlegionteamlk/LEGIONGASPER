import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from .base import BaseMemory, MemoryEntry

class DailyMemory(BaseMemory):
    
    def __init__(self, storage_path: str = "./data/memory/daily", max_entries: int = 10000):
        super().__init__("daily", max_entries)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._entries: Dict[str, MemoryEntry] = {}
        self._daily_summaries: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._loaded = False
    
    async def _ensure_loaded(self):
        
        if not self._loaded:
            await self._load_from_disk()
            self._loaded = True
    
    async def _load_from_disk(self):
        
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        file_path = self.storage_path / f"{current_date}.json"
        
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for entry_data in data.get('entries', []):
                        entry = MemoryEntry(**entry_data)
                        self._entries[entry.id] = entry
                    self._daily_summaries = data.get('summaries', {})
            except Exception:
                pass
    
    async def _save_to_disk(self):
        
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        file_path = self.storage_path / f"{current_date}.json"
        
        data = {
            'entries': [e.model_dump() for e in self._entries.values()],
            'summaries': self._daily_summaries,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, default=str)
    
    async def store(self, content: str, **kwargs) -> str:
        
        await self._ensure_loaded()
        
        async with self._lock:
            entry = self.create_entry(
                content=content,
                **kwargs
            )
            
            self._entries[entry.id] = entry
            
            if len(self._entries) % 10 == 0:
                await self._save_to_disk()
            
            return entry.id
    
    async def retrieve(self, query: str = "", limit: int = 10) -> List[MemoryEntry]:
        
        await self._ensure_loaded()
        
        async with self._lock:
            
            today = datetime.utcnow().date()
            today_entries = [
                e for e in self._entries.values()
                if e.timestamp.date() == today
            ]
            
            today_entries.sort(key=lambda x: x.timestamp, reverse=True)
            
            return today_entries[:limit]
    
    async def get_day_summary(self, date: Optional[datetime] = None) -> str:
        
        await self._ensure_loaded()
        
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y-%m-%d")
        
        async with self._lock:
            if date_str in self._daily_summaries:
                return self._daily_summaries[date_str]
            
            day_entries = [
                e for e in self._entries.values()
                if e.timestamp.strftime("%Y-%m-%d") == date_str
            ]
            
            if not day_entries:
                return f"No activity recorded for {date_str}"
            
            by_tag: Dict[str, int] = {}
            for entry in day_entries:
                for tag in entry.tags:
                    by_tag[tag] = by_tag.get(tag, 0) + 1
            
            summary = f"Activity on {date_str}:\n"
            summary += f"- Total entries: {len(day_entries)}\n"
            summary += "- Activity by tag:\n"
            for tag, count in sorted(by_tag.items(), key=lambda x: x[1], reverse=True):
                summary += f"  - {tag}: {count}\n"
            
            self._daily_summaries[date_str] = summary
            return summary
    
    async def get_recent_days(self, days: int = 7) -> List[str]:
        
        summaries = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            summary = await self.get_day_summary(date)
            summaries.append(summary)
        return summaries
    
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
            
            await self._save_to_disk()
    
    def get_stats(self) -> Dict[str, Any]:
        
        stats = super().get_stats()
        stats.update({
            "storage_path": str(self.storage_path),
            "summaries_count": len(self._daily_summaries)
        })
        return stats