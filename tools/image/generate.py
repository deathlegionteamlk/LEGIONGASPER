"""
LEGIONGASPER v2.0 - Image Generation Tool
OpenClaw-compatible image generation with multiple providers
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import requests
import base64
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import os

class ImageProvider(Enum):
    OPENAI = "openai"
    STABILITY = "stability"
    LEONARDO = "leonardo"
    LOCAL = "local"

@dataclass
class ImageResult:
    """Image generation result"""
    success: bool
    url: Optional[str] = None
    base64_data: Optional[str] = None
    local_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class ImageGenerator:
    """Multi-provider image generation"""
    
    def __init__(self,
                 openai_key: Optional[str] = None,
                 stability_key: Optional[str] = None,
                 leonardo_key: Optional[str] = None):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.stability_key = stability_key or os.getenv("STABILITY_API_KEY")
        self.leonardo_key = leonardo_key or os.getenv("LEONARDO_API_KEY")
    
    def generate_openai(self, prompt: str, 
                       size: str = "1024x1024",
                       model: str = "dall-e-3") -> ImageResult:
        """Generate image using OpenAI DALL-E"""
        if not self.openai_key:
            return ImageResult(success=False, error="OpenAI API key not configured")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1,
                "response_format": "b64_json"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                b64_data = result["data"][0]["b64_json"]
                return ImageResult(
                    success=True,
                    base64_data=b64_data,
                    metadata={
                        "provider": "openai",
                        "model": model,
                        "size": size,
                        "prompt": prompt
                    }
                )
            else:
                return ImageResult(
                    success=False,
                    error=f"API error: {response.status_code} - {response.text}"
                )
        except Exception as e:
            return ImageResult(success=False, error=str(e))
    
    def generate_stability(self, prompt: str,
                          width: int = 1024,
                          height: int = 1024) -> ImageResult:
        """Generate image using Stability AI"""
        if not self.stability_key:
            return ImageResult(success=False, error="Stability API key not configured")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.stability_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text_prompts": [{"text": prompt}],
                "width": width,
                "height": height,
                "samples": 1
            }
            
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                b64_data = result["artifacts"][0]["base64"]
                return ImageResult(
                    success=True,
                    base64_data=b64_data,
                    metadata={
                        "provider": "stability",
                        "width": width,
                        "height": height,
                        "prompt": prompt
                    }
                )
            else:
                return ImageResult(
                    success=False,
                    error=f"API error: {response.status_code}"
                )
        except Exception as e:
            return ImageResult(success=False, error=str(e))
    
    def generate(self, prompt: str,
                provider: str = "auto",
                **kwargs) -> ImageResult:
        """Generate image with specified provider"""
        
        if provider == "auto":
            # Try providers in order
            if self.openai_key:
                return self.generate_openai(prompt, **kwargs)
            elif self.stability_key:
                return self.generate_stability(prompt, **kwargs)
            else:
                return ImageResult(success=False, error="No image provider configured")
        
        elif provider == "openai":
            return self.generate_openai(prompt, **kwargs)
        
        elif provider == "stability":
            return self.generate_stability(prompt, **kwargs)
        
        else:
            return ImageResult(success=False, error=f"Unknown provider: {provider}")
    
    def save_image(self, result: ImageResult, path: str) -> bool:
        """Save generated image to file"""
        if not result.success or not result.base64_data:
            return False
        
        try:
            image_data = base64.b64decode(result.base64_data)
            with open(path, 'wb') as f:
                f.write(image_data)
            result.local_path = path
            return True
        except Exception as e:
            return False

# Global generator instance
_default_generator = ImageGenerator()

def generate(prompt: str, **kwargs) -> ImageResult:
    """Generate image"""
    return _default_generator.generate(prompt, **kwargs)

def save_image(result: ImageResult, path: str) -> bool:
    """Save image to file"""
    return _default_generator.save_image(result, path)
