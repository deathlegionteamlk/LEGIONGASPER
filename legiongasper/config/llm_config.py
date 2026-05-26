import yaml
from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum

class ModelTier(str, Enum):
    
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"

class ProviderType(str, Enum):
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"

class LLMConfig(BaseModel):
    
    model_id: str
    provider: ProviderType
    model_name: str
    
    tier: ModelTier = ModelTier.STANDARD
    context_window: int = 4096
    supports_functions: bool = True
    supports_vision: bool = False
    
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    
    avg_latency_ms: Optional[int] = None
    reliability_score: float = 0.95
    
    priority: int = 1  
    enabled: bool = True
    
    class Config:
        extra = "allow"

class RoutingRule(BaseModel):
    
    rule_id: str
    name: str
    description: str
    
    required_capabilities: List[str] = []
    min_tier: ModelTier = ModelTier.ECONOMY
    preferred_providers: List[ProviderType] = []
    
    cost_weight: float = 0.3
    quality_weight: float = 0.4
    speed_weight: float = 0.3

class LLMRouterConfig(BaseModel):
    
    default_provider: ProviderType = ProviderType.OPENAI
    default_model: str = "gpt-4"
    fallback_enabled: bool = True
    
    max_cost_per_request: float = 1.0
    daily_budget: Optional[float] = None
    budget_alert_threshold: float = 0.8
    
    enable_smart_routing: bool = True
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
    timeout_seconds: int = 60
    
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600

class LLMConfigRegistry:
    
    def __init__(self, config_path: Optional[str] = None):
        self.models: Dict[str, LLMConfig] = {}
        self.rules: Dict[str, RoutingRule] = {}
        self.router_config: LLMRouterConfig = LLMRouterConfig()
        self.config_path = config_path or "./configs/llm_config.yaml"
        self._load_config()
    
    def _load_config(self):
        
        path = Path(self.config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    if 'models' in data:
                        for model_data in data['models']:
                            model = LLMConfig(**model_data)
                            self.models[model.model_id] = model
                    if 'rules' in data:
                        for rule_data in data['rules']:
                            rule = RoutingRule(**rule_data)
                            self.rules[rule.rule_id] = rule
                    if 'router_config' in data:
                        self.router_config = LLMRouterConfig(**data['router_config'])
        else:
            self._load_defaults()
    
    def _load_defaults(self):
        
        defaults = [
            
            LLMConfig(
                model_id="gpt-4",
                provider=ProviderType.OPENAI,
                model_name="gpt-4",
                tier=ModelTier.PREMIUM,
                context_window=8192,
                input_cost_per_1k=0.03,
                output_cost_per_1k=0.06,
                priority=3
            ),
            LLMConfig(
                model_id="gpt-4-turbo",
                provider=ProviderType.OPENAI,
                model_name="gpt-4-turbo-preview",
                tier=ModelTier.PREMIUM,
                context_window=128000,
                input_cost_per_1k=0.01,
                output_cost_per_1k=0.03,
                priority=4
            ),
            LLMConfig(
                model_id="gpt-3.5-turbo",
                provider=ProviderType.OPENAI,
                model_name="gpt-3.5-turbo",
                tier=ModelTier.STANDARD,
                context_window=16385,
                input_cost_per_1k=0.0005,
                output_cost_per_1k=0.0015,
                priority=2
            ),
            
            LLMConfig(
                model_id="claude-3-opus",
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                tier=ModelTier.PREMIUM,
                context_window=200000,
                supports_vision=True,
                input_cost_per_1k=0.015,
                output_cost_per_1k=0.075,
                priority=5
            ),
            LLMConfig(
                model_id="claude-3-sonnet",
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                tier=ModelTier.STANDARD,
                context_window=200000,
                supports_vision=True,
                input_cost_per_1k=0.003,
                output_cost_per_1k=0.015,
                priority=3
            ),
            LLMConfig(
                model_id="claude-3-haiku",
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                tier=ModelTier.ECONOMY,
                context_window=200000,
                supports_vision=True,
                input_cost_per_1k=0.00025,
                output_cost_per_1k=0.00125,
                priority=1
            ),
        ]
        for model in defaults:
            self.models[model.model_id] = model
        
        self.rules["default"] = RoutingRule(
            rule_id="default",
            name="Default Routing",
            description="Default routing rule for general tasks",
            min_tier=ModelTier.ECONOMY,
            cost_weight=0.3,
            quality_weight=0.4,
            speed_weight=0.3
        )
    
    def get_model(self, model_id: str) -> Optional[LLMConfig]:
        
        return self.models.get(model_id)
    
    def get_by_tier(self, tier: ModelTier) -> List[LLMConfig]:
        
        return [m for m in self.models.values() if m.tier == tier and m.enabled]
    
    def get_by_provider(self, provider: ProviderType) -> List[LLMConfig]:
        
        return [m for m in self.models.values() if m.provider == provider and m.enabled]
    
    def select_model(self, tier: ModelTier = ModelTier.STANDARD, 
                   provider: Optional[ProviderType] = None) -> Optional[LLMConfig]:
        
        candidates = self.get_by_tier(tier)
        if provider:
            candidates = [c for c in candidates if c.provider == provider]
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x.priority, reverse=True)
        return candidates[0]
    
    def list_models(self) -> List[LLMConfig]:
        
        return list(self.models.values())
    
    def save_to_file(self, path: Optional[str] = None):
        
        save_path = Path(path or self.config_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "models": [m.model_dump() for m in self.models.values()],
            "rules": [r.model_dump() for r in self.rules.values()],
            "router_config": self.router_config.model_dump()
        }
        
        with open(save_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

_llm_registry: Optional[LLMConfigRegistry] = None

def get_llm_registry() -> LLMConfigRegistry:
    
    global _llm_registry
    if _llm_registry is None:
        _llm_registry = LLMConfigRegistry()
    return _llm_registry