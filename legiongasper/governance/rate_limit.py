import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class RateLimitStrategy(Enum):
    
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"

@dataclass
class RateLimitRule:
    
    name: str
    requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    key_func: Optional[callable] = None  

class RateLimiter:
    
    def __init__(self):
        self._rules: Dict[str, RateLimitRule] = {}
        
        self._tokens: Dict[str, float] = {}
        self._last_update: Dict[str, float] = {}
        
        self._windows: Dict[str, List[float]] = {}
        
        self._lock = asyncio.Lock()
    
    def add_rule(self, rule: RateLimitRule):
        
        self._rules[rule.name] = rule
    
    async def check(self, 
                     rule_name: str,
                     key: str,
                     cost: int = 1) -> Dict[str, Any]:
        
        rule = self._rules.get(rule_name)
        if not rule:
            return {"allowed": True, "reason": "no_rule"}
        
        composite_key = f"{rule_name}:{key}"
        now = time.time()
        
        async with self._lock:
            if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._check_token_bucket(composite_key, rule, cost, now)
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._check_sliding_window(composite_key, rule, cost, now)
            else:
                return await self._check_fixed_window(composite_key, rule, cost, now)
    
    async def _check_token_bucket(self,
                                  key: str,
                                  rule: RateLimitRule,
                                  cost: int,
                                  now: float) -> Dict[str, Any]:
        
        if key not in self._tokens:
            self._tokens[key] = rule.requests
            self._last_update[key] = now
        
        time_passed = now - self._last_update[key]
        tokens_to_add = time_passed * (rule.requests / rule.window_seconds)
        self._tokens[key] = min(rule.requests, self._tokens[key] + tokens_to_add)
        self._last_update[key] = now
        
        if self._tokens[key] >= cost:
            self._tokens[key] -= cost
            return {
                "allowed": True,
                "remaining": int(self._tokens[key]),
                "reset_time": now + (rule.window_seconds * cost / rule.requests)
            }
        else:
            retry_after = (cost - self._tokens[key]) * (rule.window_seconds / rule.requests)
            return {
                "allowed": False,
                "retry_after": retry_after,
                "remaining": 0
            }
    
    async def _check_sliding_window(self,
                                    key: str,
                                    rule: RateLimitRule,
                                    cost: int,
                                    now: float) -> Dict[str, Any]:
        
        if key not in self._windows:
            self._windows[key] = []
        
        window = self._windows[key]
        cutoff = now - rule.window_seconds
        
        window[:] = [t for t in window if t > cutoff]
        
        if len(window) + cost <= rule.requests:
            for _ in range(cost):
                window.append(now)
            return {
                "allowed": True,
                "remaining": rule.requests - len(window),
                "reset_time": window[0] + rule.window_seconds if window else now + rule.window_seconds
            }
        else:
            retry_after = (window[0] + rule.window_seconds) - now if window else rule.window_seconds
            return {
                "allowed": False,
                "retry_after": retry_after,
                "remaining": 0
            }
    
    async def _check_fixed_window(self,
                                  key: str,
                                  rule: RateLimitRule,
                                  cost: int,
                                  now: float) -> Dict[str, Any]:
        
        window_key = f"{key}:{int(now // rule.window_seconds)}"
        
        if window_key not in self._windows:
            self._windows[window_key] = []
        
        window = self._windows[window_key]
        
        if len(window) + cost <= rule.requests:
            for _ in range(cost):
                window.append(now)
            return {
                "allowed": True,
                "remaining": rule.requests - len(window),
                "reset_time": ((int(now // rule.window_seconds) + 1) * rule.window_seconds)
            }
        else:
            reset_time = ((int(now // rule.window_seconds) + 1) * rule.window_seconds)
            return {
                "allowed": False,
                "retry_after": reset_time - now,
                "remaining": 0
            }
    
    async def get_status(self, rule_name: str, key: str) -> Dict[str, Any]:
        
        rule = self._rules.get(rule_name)
        if not rule:
            return {"error": "Rule not found"}
        
        composite_key = f"{rule_name}:{key}"
        now = time.time()
        
        async with self._lock:
            if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                tokens = self._tokens.get(composite_key, rule.requests)
                return {
                    "rule": rule_name,
                    "key": key,
                    "tokens_remaining": int(tokens),
                    "limit": rule.requests,
                    "window": rule.window_seconds
                }
            else:
                window = self._windows.get(composite_key, [])
                cutoff = now - rule.window_seconds
                recent = [t for t in window if t > cutoff]
                return {
                    "rule": rule_name,
                    "key": key,
                    "requests_made": len(recent),
                    "requests_remaining": rule.requests - len(recent),
                    "limit": rule.requests,
                    "window": rule.window_seconds
                }
    
    async def reset(self, rule_name: Optional[str] = None, key: Optional[str] = None):
        
        async with self._lock:
            if rule_name and key:
                composite_key = f"{rule_name}:{key}"
                self._tokens.pop(composite_key, None)
                self._windows.pop(composite_key, None)
            elif rule_name:
                
                prefix = f"{rule_name}:"
                for k in list(self._tokens.keys()):
                    if k.startswith(prefix):
                        del self._tokens[k]
                for k in list(self._windows.keys()):
                    if k.startswith(prefix):
                        del self._windows[k]
            else:
                
                self._tokens.clear()
                self._windows.clear()

_rate_limiter: Optional[RateLimiter] = None

async def get_rate_limiter() -> RateLimiter:
    
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter