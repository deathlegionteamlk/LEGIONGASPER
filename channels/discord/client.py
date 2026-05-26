"""
LEGIONGASPER v2.0 - Discord Channel Integration
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DiscordMessage:
    """Discord message"""
    id: str
    content: str
    author: str
    channel_id: str
    timestamp: str
    attachments: List[Dict] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []

class DiscordClient:
    """Discord bot client"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.connected = False
        self.message_handlers: List[Callable] = []
        self._client = None
        
    async def connect(self):
        """Connect to Discord"""
        try:
            import discord
            
            intents = discord.Intents.default()
            intents.message_content = True
            
            class LegionDiscordClient(discord.Client):
                def __init__(inner_self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    inner_self.parent = self
                
                async def on_ready(inner_self):
                    self.connected = True
                    print(f"Discord bot connected as {inner_self.user}")
                
                async def on_message(inner_self, message):
                    if message.author == inner_self.user:
                        return
                    
                    msg = DiscordMessage(
                        id=str(message.id),
                        content=message.content,
                        author=str(message.author),
                        channel_id=str(message.channel.id),
                        timestamp=datetime.now().isoformat()
                    )
                    
                    for handler in self.message_handlers:
                        await handler(msg)
            
            self._client = LegionDiscordClient(intents=intents)
            await self._client.start(self.bot_token)
            
        except ImportError:
            print("discord.py not installed. Install with: pip install discord.py")
            return False
        except Exception as e:
            print(f"Discord connection error: {e}")
            return False
    
    async def send_message(self, channel_id: str, content: str) -> bool:
        """Send message to channel"""
        if not self._client or not self.connected:
            return False
        
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                await channel.send(content)
                return True
            return False
        except Exception as e:
            print(f"Error sending Discord message: {e}")
            return False
    
    def on_message(self, handler: Callable):
        """Register message handler"""
        self.message_handlers.append(handler)
    
    async def disconnect(self):
        """Disconnect from Discord"""
        if self._client:
            await self._client.close()
            self.connected = False
