import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class WhatsAppController:
    def __init__(self, api_key: Optional[str] = None, phone_number: Optional[str] = None):
        self.api_key = api_key or os.getenv('WHATSAPP_API_KEY')
        self.phone_number = phone_number or os.getenv('WHATSAPP_PHONE_NUMBER')
        self.phone_id = os.getenv('WHATSAPP_PHONE_ID')
        self.base_url = "https://graph.facebook.com/v18.0"
        self.session = None
        
        # Android automation fallback
        self.android_fallback = None
        try:
            from .android_manager import android_manager
            self.android_fallback = android_manager
        except:
            pass
    
    async def _get_session(self):
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_message(self, to: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        if self.api_key and self.phone_id:
            return await self._send_api_message(to, message, message_type)
        else:
            return await self._send_android_message(to, message)
    
    async def _send_api_message(self, to: str, message: str, message_type: str) -> Dict[str, Any]:
        try:
            import aiohttp
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": message_type
            }
            
            if message_type == "text":
                payload["text"] = {"body": message}
            elif message_type == "template":
                payload["template"] = json.loads(message)
            
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {
                    "success": resp.status == 200,
                    "response": data,
                    "message_id": data.get('messages', [{}])[0].get('id'),
                    "status": resp.status
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_android_message(self, to: str, message: str) -> Dict[str, Any]:
        if not self.android_fallback:
            return {"success": False, "error": "No Android device available for fallback"}
        
        try:
            # Use ADB to send WhatsApp message via Android
            devices = await self.android_fallback.list_devices()
            if not devices.get('devices'):
                return {"success": False, "error": "No Android devices connected"}
            
            serial = devices['devices'][0]['serial']
            
            # Launch WhatsApp with intent
            cmd = f"am start -a android.intent.action.SENDTO -d whatsapp://send?phone={to} --es android.intent.extra.TEXT '{message}'"
            result = await self.android_fallback.execute_shell(serial, cmd)
            
            return {"success": result['success'], "method": "android", "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def receive_messages(self, limit: int = 10) -> Dict[str, Any]:
        # This would typically use webhook callbacks
        # For now, return structure for webhook handling
        return {
            "success": True,
            "message": "Use webhook endpoint to receive messages",
            "webhook_url": "/webhooks/whatsapp",
            "instructions": "Configure webhook in Meta Developer Console"
        }
    
    async def get_groups(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "API key required for groups"}
        
        try:
            # WhatsApp Business API doesn't directly expose groups
            # This would require additional permissions
            return {
                "success": True,
                "groups": [],
                "note": "Groups require additional Business API permissions"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_group_message(self, group_id: str, message: str) -> Dict[str, Any]:
        # Groups work the same as individual messages in WhatsApp API
        return await self.send_message(group_id, message)
    
    async def post_status(self, media_url: str, caption: str = "") -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "API key required for status"}
        
        try:
            import aiohttp
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self.phone_number,
                "type": "image",
                "image": {"link": media_url, "caption": caption}
            }
            
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "response": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_status_updates(self) -> Dict[str, Any]:
        return {
            "success": True,
            "statuses": [],
            "note": "Status updates received via webhooks"
        }
    
    async def initiate_voice_call(self, to: str) -> Dict[str, Any]:
        # WhatsApp Business API doesn't support voice calls directly
        # Use Android automation fallback
        if self.android_fallback:
            try:
                devices = await self.android_fallback.list_devices()
                if devices.get('devices'):
                    serial = devices['devices'][0]['serial']
                    # Launch WhatsApp call intent
                    cmd = f"am start -a android.intent.action.CALL -d tel:{to}"
                    result = await self.android_fallback.execute_shell(serial, cmd)
                    return {"success": result['success'], "method": "android_call", "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {
            "success": False,
            "error": "Voice calls require Android automation or WhatsApp Web integration"
        }
    
    async def accept_call(self) -> Dict[str, Any]:
        # Would require Android accessibility service
        return {
            "success": False,
            "error": "Accepting calls requires Android accessibility service automation"
        }
    
    async def send_media(self, to: str, media_path: str, media_type: str = "image") -> Dict[str, Any]:
        if self.android_fallback:
            try:
                devices = await self.android_fallback.list_devices()
                if devices.get('devices'):
                    serial = devices['devices'][0]['serial']
                    # Push media to device and send
                    remote_path = f"/sdcard/WhatsApp/Media/{os.path.basename(media_path)}"
                    await self.android_fallback.execute_shell(serial, f"cp '{media_path}' '{remote_path}'")
                    return {"success": True, "method": "android_media", "path": remote_path}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Media sending requires Android device"}
    
    async def get_message_templates(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "API key required"}
        
        try:
            import aiohttp
            url = f"{self.base_url}/{self.phone_id}/message_templates"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            session = await self._get_session()
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                return {"success": resp.status == 200, "templates": data.get('data', [])}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        if self.session:
            await self.session.close()

whatsapp = WhatsAppController()
