"""
LEGIONGASPER v2.0 - Message Tool Manager
13+ messaging platform integration
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class Message:
    """Universal message format"""
    id: str
    content: str
    platform: str
    channel: str
    author: str
    timestamp: str
    attachments: List[Dict] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}

class MessageManager:
    """Unified messaging manager for 13+ platforms"""
    
    PLATFORMS = [
        "discord", "slack", "telegram", "whatsapp", "email",
        "sms", "matrix", "signal", "messenger", "teams",
        "webhook", "websocket", "pgone"
    ]
    
    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self.handlers: List[Callable] = []
        self.message_history: List[Message] = []
        
    def register_client(self, platform: str, client: Any) -> bool:
        """Register a platform client"""
        if platform in self.PLATFORMS:
            self.clients[platform] = client
            return True
        return False
    
    async def send_message(self, platform: str, channel: str, 
                          content: str, **kwargs) -> Dict[str, Any]:
        """Send message to any platform"""
        if platform not in self.clients:
            return {"success": False, "error": f"{platform} client not registered"}
        
        try:
            client = self.clients[platform]
            
            if platform == "discord":
                result = await client.send_message(channel, content)
            elif platform == "slack":
                result = client.send_message(channel, content)
            elif platform == "telegram":
                result = await client.send_message(channel, content)
            elif platform == "email":
                result = await client.send_email(channel, content, **kwargs)
            elif platform == "sms":
                result = await client.send_sms(channel, content)
            elif platform == "webhook":
                result = await client.post(channel, content)
            else:
                result = await client.send(channel, content)
            
            message = Message(
                id=f"msg_{datetime.now().timestamp()}",
                content=content,
                platform=platform,
                channel=channel,
                author="legiongasper",
                timestamp=datetime.now().isoformat(),
                metadata=kwargs
            )
            self.message_history.append(message)
            
            return {"success": True, "message_id": message.id, "platform": platform}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def broadcast(self, platforms: List[str], channel: str, 
                       content: str) -> Dict[str, Any]:
        """Broadcast message to multiple platforms"""
        results = {}
        tasks = []
        
        for platform in platforms:
            task = self.send_message(platform, channel, content)
            tasks.append((platform, task))
        
        for platform, task in tasks:
            try:
                results[platform] = await task
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)}
        
        return results
    
    def get_history(self, platform: Optional[str] = None, 
                   limit: int = 100) -> List[Message]:
        """Get message history"""
        filtered = self.message_history
        if platform:
            filtered = [m for m in filtered if m.platform == platform]
        return filtered[-limit:]
    
    def on_message(self, handler: Callable):
        """Register message handler"""
        self.handlers.append(handler)
    
    def get_platforms(self) -> List[Dict[str, Any]]:
        """Get available platforms"""
        return [
            {
                "id": p,
                "name": p.capitalize(),
                "connected": p in self.clients,
                "enabled": True
            }
            for p in self.PLATFORMS
        ]

# Global instance
_default_manager = MessageManager()

def send_message(platform: str, channel: str, content: str, **kwargs):
    """Send message to platform"""
    return _default_manager.send_message(platform, channel, content, **kwargs)

def broadcast(platforms: List[str], channel: str, content: str):
    """Broadcast to multiple platforms"""
    return _default_manager.broadcast(platforms, channel, content)

def get_platforms():
    """Get available platforms"""
    return _default_manager.get_platforms()
