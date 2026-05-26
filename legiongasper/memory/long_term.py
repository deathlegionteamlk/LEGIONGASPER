import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from .base import BaseMemory, MemoryEntry

class LongTermMemory(BaseMemory):
    
    def __init__(self, 
                 db_path: str = "./data/chroma_db",
                 collection_name: str = "legiongasper_memory",
                 max_entries: int = 100000):
        super().__init__("long_term", max_entries)
        self.db_path = db_path
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _ensure_initialized(self):
        
        if not self._initialized:
            await self._init_chroma()
            self._initialized = True
    
    async def _init_chroma(self):
        
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")
        
        self._client = chromadb.Client(
            ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.db_path
            )
        )
        
        try:
            self._collection = self._client.get_collection(self.collection_name)
        except Exception:
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _generate_id(self, content: str) -> str:
        
        return hashlib.md5(content.encode()).hexdigest()
    
    async def store(self, content: str, **kwargs) -> str:
        
        await self._ensure_initialized()
        
        entry = self.create_entry(content=content, **kwargs)
        
        async with self._lock:
            
            doc_id = self._generate_id(content)
            
            metadata = {
                "timestamp": entry.timestamp.isoformat(),
                "agent_id": entry.agent_id or "",
                "session_id": entry.session_id or "",
                "importance": entry.importance,
                "tags": ",".join(entry.tags)
            }
            metadata.update(entry.metadata)
            
            self._collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
            
            self._entries[entry.id] = entry
            
            return entry.id
    
    async def retrieve(self, query: str, limit: int = 10, 
                      filter_dict: Optional[Dict] = None) -> List[MemoryEntry]:
        
        await self._ensure_initialized()
        
        async with self._lock:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_dict
            )
            
            entries = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    entry = MemoryEntry(
                        id=results['ids'][0][i],
                        content=doc,
                        timestamp=datetime.fromisoformat(metadata.get('timestamp', datetime.utcnow().isoformat())),
                        agent_id=metadata.get('agent_id') or None,
                        session_id=metadata.get('session_id') or None,
                        importance=metadata.get('importance', 1.0),
                        tags=metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                        metadata={"distance": distance, **metadata}
                    )
                    entries.append(entry)
            
            return entries
    
    async def search_by_tag(self, tag: str, limit: int = 10) -> List[MemoryEntry]:
        
        return await self.retrieve(
            query="",
            limit=limit,
            filter_dict={"tags": {"$contains": tag}}
        )
    
    async def search_by_agent(self, agent_id: str, limit: int = 10) -> List[MemoryEntry]:
        
        return await self.retrieve(
            query="",
            limit=limit,
            filter_dict={"agent_id": agent_id}
        )
    
    async def delete_by_id(self, entry_id: str):
        
        await self._ensure_initialized()
        
        async with self._lock:
            try:
                self._collection.delete(ids=[entry_id])
                if entry_id in self._entries:
                    del self._entries[entry_id]
            except Exception:
                pass
    
    async def clear(self, agent_id: Optional[str] = None):
        
        await self._ensure_initialized()
        
        async with self._lock:
            if agent_id:
                
                self._collection.delete(
                    where={"agent_id": agent_id}
                )
            else:
                
                self._collection.delete()
            
            self._entries.clear()
    
    async def get_similar(self, content: str, threshold: float = 0.8) -> List[MemoryEntry]:
        
        entries = await self.retrieve(content, limit=20)
        
        similar = [
            e for e in entries
            if e.metadata.get('distance', 1.0) < (1 - threshold)
        ]
        
        return similar
    
    def get_stats(self) -> Dict[str, Any]:
        
        stats = super().get_stats()
        stats.update({
            "db_path": self.db_path,
            "collection_name": self.collection_name,
            "chromadb_available": CHROMADB_AVAILABLE
        })
        return stats