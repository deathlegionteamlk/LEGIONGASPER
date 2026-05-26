"""
LEGIONGASPER v2.0 - Venice AI Integration
Privacy-focused LLM with zero-knowledge requests
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass
import os
import requests

@dataclass
class VeniceConfig:
    """Venice AI configuration"""
    api_key: str
    base_url: str = "https://api.venice.ai"
    model: str = "llama-3.3-70b"
    temperature: float = 0.7
    max_tokens: int = 4096
    enable_private_mode: bool = True

class VeniceClient:
    """Venice AI privacy-focused LLM client"""
    
    AVAILABLE_MODELS = [
        "llama-3.3-70b",
        "llama-3.1-405b",
        "dolphin-2.9.2-qwen2-72b",
        "qwen2.5-coder-32b",
        "deepseek-coder-v2-lite"
    ]
    
    def __init__(self, config: Optional[VeniceConfig] = None):
        self.config = config or VeniceConfig(
            api_key=os.getenv("VENICE_API_KEY", "")
        )
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with privacy settings"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.config.enable_private_mode:
            headers["X-Venice-Private"] = "true"
            headers["X-Venice-No-Training"] = "true"
        
        return headers
    
    def chat(self, messages: List[Dict[str, str]], 
             **kwargs) -> Dict[str, Any]:
        """Send chat completion request"""
        try:
            payload = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "stream": False
            }
            
            response = self.session.post(
                f"{self.config.base_url}/api/v1/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "model": payload["model"],
                    "privacy_mode": self.config.enable_private_mode
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stream_chat(self, messages: List[Dict[str, str]], 
                   **kwargs) -> Generator[str, None, None]:
        """Stream chat completion"""
        try:
            payload = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "stream": True
            }
            
            response = self.session.post(
                f"{self.config.base_url}/api/v1/chat/completions",
                headers=self._get_headers(),
                json=payload,
                stream=True,
                timeout=60
            )
            
            for line in response.iter_lines():
                if line:
                    yield line.decode('utf-8')
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image using Venice AI"""
        try:
            payload = {
                "prompt": prompt,
                "model": kwargs.get("model", "fluently-xl"),
                "width": kwargs.get("width", 1024),
                "height": kwargs.get("height", 1024),
                "steps": kwargs.get("steps", 30),
                "cfg_scale": kwargs.get("cfg_scale", 7.5)
            }
            
            response = self.session.post(
                f"{self.config.base_url}/api/v1/image/generate",
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available Venice AI models"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/v1/models",
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                # Return default models
                return [
                    {"id": m, "name": m.replace("-", " ").title()}
                    for m in self.AVAILABLE_MODELS
                ]
                
        except Exception:
            return [
                {"id": m, "name": m.replace("-", " ").title()}
                for m in self.AVAILABLE_MODELS
            ]
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get VVV token information"""
        return {
            "token_type": "VVV",
            "privacy_features": [
                "Zero-knowledge requests",
                "No training data retention",
                "Encrypted inference",
                "No logs mode"
            ],
            "supported_models": self.AVAILABLE_MODELS
        }

# Global client
_default_client = None

def get_client(api_key: Optional[str] = None) -> VeniceClient:
    """Get Venice AI client"""
    global _default_client
    if _default_client is None:
        config = VeniceConfig(api_key=api_key or os.getenv("VENICE_API_KEY", ""))
        _default_client = VeniceClient(config)
    return _default_client

def chat(messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
    """Send chat request"""
    return get_client().chat(messages, **kwargs)

def generate_image(prompt: str, **kwargs) -> Dict[str, Any]:
    """Generate image"""
    return get_client().generate_image(prompt, **kwargs)
