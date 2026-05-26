import os
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

class VeniceAI:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.venice.ai"):
        self.api_key = api_key or os.getenv('VENICE_API_KEY')
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.default_model = "llama-3.3-70b"
        
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def list_models(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "VENICE_API_KEY not set"}
        
        url = f"{self.base_url}/api/v1/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            session = await self._get_session()
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                return {
                    "success": resp.status == 200,
                    "models": data.get('data', []),
                    "status": resp.status
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, 
                              temperature: float = 0.7, max_tokens: int = 1024) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "VENICE_API_KEY not set"}
        
        url = f"{self.base_url}/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {
                    "success": resp.status == 200,
                    "response": data,
                    "content": data.get('choices', [{}])[0].get('message', {}).get('content', ''),
                    "model": model or self.default_model,
                    "status": resp.status
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def stream_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                                temperature: float = 0.7, max_tokens: int = 1024) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "Error: VENICE_API_KEY not set"
            return
        
        url = f"{self.base_url}/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        except:
                            pass
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def generate_image(self, prompt: str, model: str = "flux-dev", width: int = 1024, height: int = 1024) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "VENICE_API_KEY not set"}
        
        url = f"{self.base_url}/api/v1/image/generate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                return {
                    "success": resp.status == 200,
                    "images": data.get('images', []),
                    "status": resp.status
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        if self.session:
            await self.session.close()

venice_ai = VeniceAI()
