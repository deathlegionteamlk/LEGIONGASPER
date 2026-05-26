"""
LEGIONGASPER v2.0 - Capy.ai Parallel Agent Slots
25 parallel agent execution with slot management
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading

class SlotStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class AgentSlot:
    """Agent execution slot"""
    id: int
    status: SlotStatus
    agent_id: Optional[str] = None
    task: Optional[str] = None
    started_at: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

class SlotManager:
    """Manages 25 parallel agent slots"""
    
    MAX_SLOTS = 25
    
    def __init__(self):
        self.slots: Dict[int, AgentSlot] = {
            i: AgentSlot(id=i, status=SlotStatus.IDLE)
            for i in range(1, self.MAX_SLOTS + 1)
        }
        self._lock = threading.RLock()
        self._semaphore = asyncio.Semaphore(self.MAX_SLOTS)
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[int, asyncio.Task] = {}
        
    def get_available_slots(self) -> List[int]:
        """Get list of available slot IDs"""
        with self._lock:
            return [
                slot.id for slot in self.slots.values()
                if slot.status == SlotStatus.IDLE
            ]
    
    def get_slot(self, slot_id: int) -> Optional[AgentSlot]:
        """Get slot by ID"""
        return self.slots.get(slot_id)
    
    def assign_agent(self, slot_id: int, agent_id: str, 
                    task: str, metadata: Optional[Dict] = None) -> bool:
        """Assign agent to slot"""
        with self._lock:
            slot = self.slots.get(slot_id)
            if not slot or slot.status != SlotStatus.IDLE:
                return False
            
            slot.status = SlotStatus.BUSY
            slot.agent_id = agent_id
            slot.task = task
            slot.started_at = datetime.now().isoformat()
            slot.metadata = metadata or {}
            return True
    
    def release_slot(self, slot_id: int) -> bool:
        """Release slot"""
        with self._lock:
            slot = self.slots.get(slot_id)
            if not slot:
                return False
            
            slot.status = SlotStatus.IDLE
            slot.agent_id = None
            slot.task = None
            slot.started_at = None
            slot.metadata = {}
            return True
    
    async def execute_in_slot(self, slot_id: int, 
                             coro: Callable, *args, **kwargs) -> Any:
        """Execute coroutine in slot with semaphore"""
        async with self._semaphore:
            if slot_id not in self.slots:
                raise ValueError(f"Invalid slot ID: {slot_id}")
            
            slot = self.slots[slot_id]
            if slot.status != SlotStatus.IDLE:
                raise RuntimeError(f"Slot {slot_id} is not available")
            
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                slot.status = SlotStatus.ERROR
                raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get slot manager status"""
        with self._lock:
            return {
                "total_slots": self.MAX_SLOTS,
                "available": len(self.get_available_slots()),
                "busy": sum(1 for s in self.slots.values() if s.status == SlotStatus.BUSY),
                "paused": sum(1 for s in self.slots.values() if s.status == SlotStatus.PAUSED),
                "error": sum(1 for s in self.slots.values() if s.status == SlotStatus.ERROR),
                "slots": [
                    {
                        "id": s.id,
                        "status": s.status.value,
                        "agent_id": s.agent_id,
                        "task": s.task
                    }
                    for s in self.slots.values()
                ]
            }
    
    def pause_slot(self, slot_id: int) -> bool:
        """Pause slot execution"""
        with self._lock:
            slot = self.slots.get(slot_id)
            if slot and slot.status == SlotStatus.BUSY:
                slot.status = SlotStatus.PAUSED
                return True
            return False
    
    def resume_slot(self, slot_id: int) -> bool:
        """Resume slot execution"""
        with self._lock:
            slot = self.slots.get(slot_id)
            if slot and slot.status == SlotStatus.PAUSED:
                slot.status = SlotStatus.BUSY
                return True
            return False

# Global instance
_default_manager = SlotManager()

def get_slot_manager() -> SlotManager:
    """Get default slot manager"""
    return _default_manager

def get_available_slots() -> List[int]:
    """Get available slots"""
    return _default_manager.get_available_slots()
