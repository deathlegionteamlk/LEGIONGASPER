import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from abc import ABC, abstractmethod

class BaseWebhookClient(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    @abstractmethod
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    async def close(self):
        if self.session:
            await self.session.close()

class WhatsAppClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        api_key = self.config.get('api_key')
        phone_id = self.config.get('phone_id')
        if not api_key or not phone_id:
            return {"success": False, "error": "Missing API key or phone ID"}
        
        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "response": data, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if messages:
                msg = messages[0]
                return {
                    "platform": "whatsapp",
                    "from": msg.get('from'),
                    "text": msg.get('text', {}).get('body'),
                    "timestamp": msg.get('timestamp'),
                    "type": msg.get('type'),
                    "raw": payload
                }
            return {"platform": "whatsapp", "type": "status", "raw": payload}
        except Exception as e:
            return {"platform": "whatsapp", "error": str(e), "raw": payload}

class TelegramClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        bot_token = self.config.get('bot_token')
        if not bot_token:
            return {"success": False, "error": "Missing bot token"}
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": recipient,
            "text": message,
            "parse_mode": kwargs.get('parse_mode', 'HTML')
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return {"success": data.get('ok', False), "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            message = payload.get('message', {})
            return {
                "platform": "telegram",
                "from": message.get('from', {}).get('id'),
                "username": message.get('from', {}).get('username'),
                "text": message.get('text'),
                "chat_id": message.get('chat', {}).get('id'),
                "timestamp": message.get('date'),
                "raw": payload
            }
        except Exception as e:
            return {"platform": "telegram", "error": str(e), "raw": payload}

class DiscordClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        webhook_url = self.config.get('webhook_url')
        bot_token = self.config.get('bot_token')
        
        if webhook_url:
            payload = {"content": message}
            if kwargs.get('embeds'):
                payload['embeds'] = kwargs['embeds']
            try:
                session = await self._get_session()
                async with session.post(webhook_url, json=payload) as resp:
                    return {"success": resp.status in [200, 204], "status": resp.status}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif bot_token:
            channel_id = recipient
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
            payload = {"content": message}
            try:
                session = await self._get_session()
                async with session.post(url, headers=headers, json=payload) as resp:
                    data = await resp.json()
                    return {"success": resp.status == 200, "response": data}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Missing webhook_url or bot_token"}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                "platform": "discord",
                "type": payload.get('type'),
                "token": payload.get('token'),
                "data": payload.get('data', {}),
                "raw": payload
            }
        except Exception as e:
            return {"platform": "discord", "error": str(e), "raw": payload}

class SlackClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        webhook_url = self.config.get('webhook_url')
        bot_token = self.config.get('bot_token')
        
        if webhook_url:
            payload = {"text": message}
            if kwargs.get('blocks'):
                payload['blocks'] = kwargs['blocks']
            try:
                session = await self._get_session()
                async with session.post(webhook_url, json=payload) as resp:
                    return {"success": resp.status == 200, "status": resp.status}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif bot_token:
            url = "https://slack.com/api/chat.postMessage"
            headers = {"Authorization": f"Bearer {bot_token}", "Content-Type": "application/json"}
            payload = {"channel": recipient, "text": message}
            try:
                session = await self._get_session()
                async with session.post(url, headers=headers, json=payload) as resp:
                    data = await resp.json()
                    return {"success": data.get('ok', False), "response": data}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Missing webhook_url or bot_token"}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return {
                "platform": "slack",
                "type": payload.get('type'),
                "user": payload.get('user'),
                "text": payload.get('text'),
                "channel": payload.get('channel'),
                "timestamp": payload.get('ts'),
                "raw": payload
            }
        except Exception as e:
            return {"platform": "slack", "error": str(e), "raw": payload}

class TeamsClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return {"success": False, "error": "Missing webhook URL"}
        
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "text": message
        }
        if kwargs.get('title'):
            payload['title'] = kwargs['title']
        
        try:
            session = await self._get_session()
            async with session.post(webhook_url, json=payload) as resp:
                return {"success": resp.status in [200, 202], "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "teams", "raw": payload}

class MessengerClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        page_token = self.config.get('page_token')
        if not page_token:
            return {"success": False, "error": "Missing page token"}
        
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={page_token}"
        payload = {
            "recipient": {"id": recipient},
            "message": {"text": message}
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            entry = payload.get('entry', [{}])[0]
            messaging = entry.get('messaging', [{}])[0]
            return {
                "platform": "messenger",
                "sender": messaging.get('sender', {}).get('id'),
                "text": messaging.get('message', {}).get('text'),
                "timestamp": messaging.get('timestamp'),
                "raw": payload
            }
        except Exception as e:
            return {"platform": "messenger", "error": str(e), "raw": payload}

class SignalClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        api_url = self.config.get('api_url', 'http://localhost:8080')
        number = self.config.get('number')
        
        if not number:
            return {"success": False, "error": "Missing Signal number"}
        
        url = f"{api_url}/v2/send"
        payload = {
            "message": message,
            "number": number,
            "recipients": [recipient]
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                return {"success": resp.status == 200, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "signal", "raw": payload}

class MatrixClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        homeserver = self.config.get('homeserver')
        access_token = self.config.get('access_token')
        
        if not homeserver or not access_token:
            return {"success": False, "error": "Missing homeserver or access token"}
        
        room_id = recipient
        url = f"{homeserver}/_matrix/client/r0/rooms/{room_id}/send/m.room.message"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "msgtype": "m.text",
            "body": message
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "matrix", "raw": payload}

class RocketChatClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        server_url = self.config.get('server_url')
        auth_token = self.config.get('auth_token')
        user_id = self.config.get('user_id')
        
        if not all([server_url, auth_token, user_id]):
            return {"success": False, "error": "Missing server_url, auth_token, or user_id"}
        
        url = f"{server_url}/api/v1/chat.postMessage"
        headers = {
            "X-Auth-Token": auth_token,
            "X-User-Id": user_id,
            "Content-Type": "application/json"
        }
        payload = {"channel": recipient, "text": message}
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"success": data.get('success', False), "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "rocketchat", "raw": payload}

class MattermostClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return {"success": False, "error": "Missing webhook URL"}
        
        payload = {
            "text": message,
            "channel": recipient
        }
        if kwargs.get('username'):
            payload['username'] = kwargs['username']
        
        try:
            session = await self._get_session()
            async with session.post(webhook_url, json=payload) as resp:
                return {"success": resp.status == 200, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "mattermost", "raw": payload}

class ZulipClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        site = self.config.get('site')
        bot_email = self.config.get('bot_email')
        api_key = self.config.get('api_key')
        
        if not all([site, bot_email, api_key]):
            return {"success": False, "error": "Missing site, bot_email, or api_key"}
        
        url = f"{site}/api/v1/messages"
        payload = {
            "type": kwargs.get('type', 'stream'),
            "to": recipient,
            "content": message
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, auth=aiohttp.BasicAuth(bot_email, api_key), data=payload) as resp:
                data = await resp.json()
                return {"success": data.get('result') == 'success', "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "zulip", "raw": payload}

class WebexClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        access_token = self.config.get('access_token')
        if not access_token:
            return {"success": False, "error": "Missing access token"}
        
        url = "https://webexapis.com/v1/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "toPersonEmail" if '@' in recipient else "roomId": recipient,
            "text": message
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "webex", "raw": payload}

class InstagramClient(BaseWebhookClient):
    async def send_message(self, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        access_token = self.config.get('access_token')
        if not access_token:
            return {"success": False, "error": "Missing access token"}
        
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={access_token}"
        payload = {
            "recipient": {"id": recipient},
            "message": {"text": message}
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": "instagram", "raw": payload}

class WebhookManager:
    def __init__(self):
        self.clients: Dict[str, BaseWebhookClient] = {}
        self.handlers: Dict[str, List[Callable]] = {}
        
    def register_client(self, name: str, client: BaseWebhookClient):
        self.clients[name] = client
        self.handlers[name] = []
        
    def get_client(self, name: str) -> Optional[BaseWebhookClient]:
        return self.clients.get(name)
    
    def create_client(self, platform: str, config: Dict[str, Any]) -> BaseWebhookClient:
        clients = {
            'whatsapp': WhatsAppClient,
            'telegram': TelegramClient,
            'discord': DiscordClient,
            'slack': SlackClient,
            'teams': TeamsClient,
            'messenger': MessengerClient,
            'signal': SignalClient,
            'matrix': MatrixClient,
            'rocketchat': RocketChatClient,
            'mattermost': MattermostClient,
            'zulip': ZulipClient,
            'webex': WebexClient,
            'instagram': InstagramClient
        }
        
        client_class = clients.get(platform.lower())
        if not client_class:
            raise ValueError(f"Unknown platform: {platform}")
        
        return client_class(config)
    
    async def send_message(self, platform: str, recipient: str, message: str, **kwargs) -> Dict[str, Any]:
        client = self.clients.get(platform)
        if not client:
            return {"success": False, "error": f"Client not registered for {platform}"}
        return await client.send_message(recipient, message, **kwargs)
    
    async def handle_webhook(self, platform: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        client = self.clients.get(platform)
        if not client:
            return {"success": False, "error": f"Client not registered for {platform}"}
        
        parsed = await client.parse_webhook(payload)
        
        for handler in self.handlers.get(platform, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(parsed)
                else:
                    handler(parsed)
            except Exception as e:
                print(f"Handler error: {e}")
        
        return parsed
    
    def on_message(self, platform: str):
        def decorator(func):
            if platform not in self.handlers:
                self.handlers[platform] = []
            self.handlers[platform].append(func)
            return func
        return decorator
    
    async def close_all(self):
        for client in self.clients.values():
            await client.close()

webhook_manager = WebhookManager()
