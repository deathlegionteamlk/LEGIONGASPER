"""
LEGIONGASPER v2.0 - Slack Channel Integration
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
import requests

@dataclass
class SlackMessage:
    """Slack message"""
    id: str
    content: str
    author: str
    channel: str
    timestamp: str
    thread_ts: Optional[str] = None

class SlackClient:
    """Slack bot client"""
    
    def __init__(self, bot_token: str, signing_secret: Optional[str] = None):
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.connected = False
        self.message_handlers: List[Callable] = []
        self._client = None
        
    def connect(self) -> bool:
        """Connect to Slack"""
        try:
            from slack_sdk import WebClient
            from slack_sdk.socket_mode import SocketModeClient
            
            self._client = WebClient(token=self.bot_token)
            
            # Test connection
            auth_test = self._client.auth_test()
            self.connected = auth_test["ok"]
            
            return self.connected
            
        except ImportError:
            print("slack-sdk not installed. Install with: pip install slack-sdk")
            return False
        except Exception as e:
            print(f"Slack connection error: {e}")
            return False
    
    def send_message(self, channel: str, text: str, 
                   blocks: Optional[List[Dict]] = None) -> bool:
        """Send message to channel"""
        if not self._client:
            return False
        
        try:
            kwargs = {"channel": channel, "text": text}
            if blocks:
                kwargs["blocks"] = blocks
            
            self._client.chat_postMessage(**kwargs)
            return True
        except Exception as e:
            print(f"Error sending Slack message: {e}")
            return False
    
    def send_dm(self, user_id: str, text: str) -> bool:
        """Send direct message"""
        return self.send_message(user_id, text)
    
    def get_channel_list(self) -> List[Dict[str, Any]]:
        """Get list of channels"""
        if not self._client:
            return []
        
        try:
            result = self._client.conversations_list()
            return [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "is_private": ch.get("is_private", False)
                }
                for ch in result["channels"]
            ]
        except Exception as e:
            print(f"Error getting channels: {e}")
            return []
    
    def on_message(self, handler: Callable):
        """Register message handler"""
        self.message_handlers.append(handler)
