import asyncio
import time
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..config import get_llm_registry, get_settings, ModelTier, ProviderType
from .providers import (
    BaseProvider, OpenAIProvider, AnthropicProvider, 
    OpenRouterProvider, LLMRequest, LLMResponse, Message
)

class RoutingStrategy(Enum):
    
    SIMPLE = "simple"  
    COST_OPTIMIZED = "cost"  
    QUALITY_OPTIMIZED = "quality"  
    BALANCED = "balanced"  
    FALLBACK = "fallback"  

@dataclass
class RoutingDecision:
    
    provider: str
    model: str
    reason: str
    estimated_cost: float

@dataclass
class RouterStats:
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    provider_usage: Dict[str, int] = field(default_factory=dict)

class LLMRouter:
    
    def __init__(self):
        self.settings = get_settings()
        self.config = get_llm_registry()
        
        self._providers: Dict[str, BaseProvider] = {}
        self._provider_lock = asyncio.Lock()
        
        self._stats = RouterStats()
        self._daily_cost = 0.0
        self._cost_lock = asyncio.Lock()
        
        self._cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()
        
        self._logger = logging.getLogger(__name__)
    
    async def initialize(self):
        
        if self.settings.openai_api_key:
            try:
                provider = OpenAIProvider()
                await provider.initialize()
                async with self._provider_lock:
                    self._providers["openai"] = provider
                self._logger.info("OpenAI provider registered")
            except Exception as e:
                self._logger.warning(f"Failed to initialize OpenAI: {e}")
        
        if self.settings.anthropic_api_key:
            try:
                provider = AnthropicProvider()
                await provider.initialize()
                async with self._provider_lock:
                    self._providers["anthropic"] = provider
                self._logger.info("Anthropic provider registered")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Anthropic: {e}")
        
        if self.settings.openrouter_api_key:
            try:
                provider = OpenRouterProvider()
                await provider.initialize()
                async with self._provider_lock:
                    self._providers["openrouter"] = provider
                self._logger.info("OpenRouter provider registered")
            except Exception as e:
                self._logger.warning(f"Failed to initialize OpenRouter: {e}")
        
        if not self._providers:
            self._logger.warning("No LLM providers initialized!")
    
    async def _get_provider(self, provider_name: str) -> Optional[BaseProvider]:
        
        async with self._provider_lock:
            return self._providers.get(provider_name)
    
    async def _route(self, 
                     tier: ModelTier = ModelTier.STANDARD,
                     preferred_provider: Optional[str] = None,
                     strategy: RoutingStrategy = RoutingStrategy.BALANCED) -> RoutingDecision:
        
        models = self.config.get_by_tier(tier)
        
        if not models:
            
            models = self.config.list_models()
        
        available_models = []
        async with self._provider_lock:
            for model in models:
                if model.provider.value in self._providers:
                    available_models.append(model)
        
        if not available_models:
            raise RuntimeError("No LLM providers available")
        
        if strategy == RoutingStrategy.SIMPLE or preferred_provider:
            
            for model in available_models:
                if preferred_provider is None or model.provider.value == preferred_provider:
                    return RoutingDecision(
                        provider=model.provider.value,
                        model=model.model_name,
                        reason="simple routing",
                        estimated_cost=model.input_cost_per_1k + model.output_cost_per_1k
                    )
        
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            
            available_models.sort(key=lambda m: m.input_cost_per_1k + m.output_cost_per_1k)
            model = available_models[0]
            return RoutingDecision(
                provider=model.provider.value,
                model=model.model_name,
                reason="cost optimized",
                estimated_cost=model.input_cost_per_1k + model.output_cost_per_1k
            )
        
        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            
            available_models.sort(key=lambda m: m.priority, reverse=True)
            model = available_models[0]
            return RoutingDecision(
                provider=model.provider.value,
                model=model.model_name,
                reason="quality optimized",
                estimated_cost=model.input_cost_per_1k + model.output_cost_per_1k
            )
        
        best_score = -1
        best_model = available_models[0]
        
        for model in available_models:
            
            cost_score = 1 - min(model.input_cost_per_1k / 0.1, 1)  
            quality_score = model.priority / 5  
            reliability_score = model.reliability_score
            
            score = (0.3 * cost_score + 0.4 * quality_score + 0.3 * reliability_score)
            
            if score > best_score:
                best_score = score
                best_model = model
        
        return RoutingDecision(
            provider=best_model.provider.value,
            model=best_model.model_name,
            reason="balanced routing",
            estimated_cost=best_model.input_cost_per_1k + best_model.output_cost_per_1k
        )
    
    async def complete(self,
                      messages: List[Message],
                      tier: ModelTier = ModelTier.STANDARD,
                      preferred_provider: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: int = 2000,
                      strategy: RoutingStrategy = RoutingStrategy.BALANCED) -> LLMResponse:
        
        async with self._cost_lock:
            if self.settings.daily_budget and self._daily_cost >= self.settings.daily_budget:
                raise RuntimeError("Daily budget exceeded")
        
        decision = await self._route(tier, preferred_provider, strategy)
        
        provider = await self._get_provider(decision.provider)
        if not provider:
            raise RuntimeError(f"Provider not available: {decision.provider}")
        
        request = LLMRequest(
            messages=messages,
            model=decision.model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        max_retries = self.settings.retry_attempts
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await provider.complete(request)
                
                await self._update_stats(response, decision.provider)
                
                return response
                
            except Exception as e:
                last_error = e
                self._logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(self.settings.retry_delay_seconds * (attempt + 1))
                
                if strategy == RoutingStrategy.FALLBACK:
                    for prov_name in ["openai", "anthropic", "openrouter"]:
                        if prov_name != decision.provider:
                            fallback = await self._get_provider(prov_name)
                            if fallback:
                                self._logger.info(f"Trying fallback provider: {prov_name}")
                                try:
                                    response = await fallback.complete(request)
                                    await self._update_stats(response, prov_name)
                                    return response
                                except Exception:
                                    continue
        
        raise last_error or RuntimeError("All retries failed")
    
    async def stream(self,
                    messages: List[Message],
                    tier: ModelTier = ModelTier.STANDARD,
                    preferred_provider: Optional[str] = None,
                    temperature: float = 0.7,
                    max_tokens: int = 2000) -> AsyncGenerator[str, None]:
        
        decision = await self._route(tier, preferred_provider, RoutingStrategy.SIMPLE)
        
        provider = await self._get_provider(decision.provider)
        if not provider:
            raise RuntimeError(f"Provider not available: {decision.provider}")
        
        request = LLMRequest(
            messages=messages,
            model=decision.model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in provider.stream(request):
            yield chunk
    
    async def _update_stats(self, response: LLMResponse, provider: str):
        
        async with self._cost_lock:
            self._stats.total_requests += 1
            self._stats.successful_requests += 1
            self._stats.total_cost += response.cost
            self._daily_cost += response.cost
            
            if provider not in self._stats.provider_usage:
                self._stats.provider_usage[provider] = 0
            self._stats.provider_usage[provider] += 1
            
            total_latency = self._stats.avg_latency_ms * (self._stats.total_requests - 1)
            self._stats.avg_latency_ms = (total_latency + response.latency_ms) / self._stats.total_requests
    
    async def get_stats(self) -> Dict[str, Any]:
        
        return {
            "total_requests": self._stats.total_requests,
            "successful_requests": self._stats.successful_requests,
            "failed_requests": self._stats.failed_requests,
            "total_cost": round(self._stats.total_cost, 4),
            "daily_cost": round(self._daily_cost, 4),
            "avg_latency_ms": round(self._stats.avg_latency_ms, 2),
            "provider_usage": self._stats.provider_usage,
            "available_providers": list(self._providers.keys())
        }
    
    async def reset_daily_cost(self):
        
        async with self._cost_lock:
            self._daily_cost = 0.0
    
    def get_available_providers(self) -> List[str]:
        
        return list(self._providers.keys())

_router: Optional[LLMRouter] = None

async def get_llm_router() -> LLMRouter:
    
    global _router
    if _router is None:
        _router = LLMRouter()
        await _router.initialize()
    return _router