import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
import logging

from ..config import get_settings

@dataclass
class Message:
    
    role: str  
    content: str

@dataclass
class LLMRequest:
    
    messages: List[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = False

@dataclass
class LLMResponse:
    
    content: str
    model: str
    provider: str
    usage: Dict[str, int]
    cost: float
    latency_ms: float

class BaseProvider(ABC):
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.settings = get_settings()
        self._logger = logging.getLogger(f"{__name__}.{provider_name}")
        self._client = None
    
    @abstractmethod
    async def initialize(self):
        
        pass
    
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        
        pass
    
    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        
        pass
    
    @abstractmethod
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        
        pass

class OpenAIProvider(BaseProvider):
    
    def __init__(self):
        super().__init__("openai")
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }
    
    async def initialize(self):
        
        try:
            from openai import AsyncOpenAI
            api_key = self.settings.openai_api_key
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            self._client = AsyncOpenAI(api_key=api_key)
            self._logger.info("OpenAI provider initialized")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        
        import time
        
        if not self._client:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            response = await self._client.chat.completions.create(
                model=request.model,
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            content = response.choices[0].message.content
            usage = response.usage
            
            cost = self.calculate_cost(
                request.model,
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                cost=cost,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            self._logger.error(f"OpenAI completion error: {e}")
            raise
    
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        
        if not self._client:
            await self.initialize()
        
        try:
            stream = await self._client.chat.completions.create(
                model=request.model,
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self._logger.error(f"OpenAI stream error: {e}")
            raise
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        
        pricing = self.pricing.get(model, {"input": 0.03, "output": 0.06})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

class AnthropicProvider(BaseProvider):
    
    def __init__(self):
        super().__init__("anthropic")
        self.pricing = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
    
    async def initialize(self):
        
        try:
            from anthropic import AsyncAnthropic
            api_key = self.settings.anthropic_api_key
            if not api_key:
                raise ValueError("Anthropic API key not configured")
            self._client = AsyncAnthropic(api_key=api_key)
            self._logger.info("Anthropic provider initialized")
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        
        import time
        
        if not self._client:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            
            system_msg = ""
            messages = []
            for m in request.messages:
                if m.role == "system":
                    system_msg = m.content
                else:
                    messages.append({"role": m.role, "content": m.content})
            
            response = await self._client.messages.create(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system_msg,
                messages=messages
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            content = response.content[0].text
            usage = response.usage
            
            cost = self.calculate_cost(
                request.model,
                usage.input_tokens,
                usage.output_tokens
            )
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": usage.input_tokens,
                    "completion_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens
                },
                cost=cost,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            self._logger.error(f"Anthropic completion error: {e}")
            raise
    
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        
        if not self._client:
            await self.initialize()
        
        try:
            system_msg = ""
            messages = []
            for m in request.messages:
                if m.role == "system":
                    system_msg = m.content
                else:
                    messages.append({"role": m.role, "content": m.content})
            
            async with self._client.messages.stream(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system_msg,
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            self._logger.error(f"Anthropic stream error: {e}")
            raise
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        
        pricing = self.pricing.get(model, {"input": 0.003, "output": 0.015})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

class OpenRouterProvider(BaseProvider):
    
    def __init__(self):
        super().__init__("openrouter")
        self.pricing = {}  
    
    async def initialize(self):
        
        try:
            import aiohttp
            api_key = self.settings.openrouter_api_key
            if not api_key:
                raise ValueError("OpenRouter API key not configured")
            self._api_key = api_key
            self._session = aiohttp.ClientSession()
            self._logger.info("OpenRouter provider initialized")
        except ImportError:
            raise ImportError("aiohttp package not installed. Run: pip install aiohttp")
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        
        import time
        
        if not hasattr(self, '_session'):
            await self.initialize()
        
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
            
            async with self._session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()
                
                latency_ms = (time.time() - start_time) * 1000
                
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                
                cost = result.get("cost", 0.0)
                
                return LLMResponse(
                    content=content,
                    model=request.model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    },
                    cost=cost,
                    latency_ms=latency_ms
                )
                
        except Exception as e:
            self._logger.error(f"OpenRouter completion error: {e}")
            raise
    
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        
        if not hasattr(self, '_session'):
            await self.initialize()
        
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": request.model,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": True
            }
            
            async with self._session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            if chunk.get('choices'):
                                delta = chunk['choices'][0].get('delta', {})
                                if delta.get('content'):
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            self._logger.error(f"OpenRouter stream error: {e}")
            raise
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        
        return 0.0  