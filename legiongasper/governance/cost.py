import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CostReport:
    
    total_cost: float
    period: str
    by_provider: Dict[str, float]
    by_agent: Dict[str, float]
    by_model: Dict[str, float]
    request_count: int
    token_count: int
    start_time: datetime
    end_time: datetime

class CostTracker:
    
    def __init__(self, 
                 daily_budget: Optional[float] = None,
                 alert_threshold: float = 0.8):
        
        self.daily_budget = daily_budget
        self.alert_threshold = alert_threshold
        
        self._costs: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        
        self._daily_costs: Dict[str, float] = defaultdict(float)
        self._provider_costs: Dict[str, float] = defaultdict(float)
        self._agent_costs: Dict[str, float] = defaultdict(float)
        self._model_costs: Dict[str, float] = defaultdict(float)
        
        self._request_count = 0
        self._token_count = 0
        
        self._alert_sent_today = False
    
    async def record_cost(self,
                         amount: float,
                         provider: str,
                         model: str,
                         agent_id: str,
                         tokens_in: int = 0,
                         tokens_out: int = 0,
                         request_type: str = "llm"):
        
        async with self._lock:
            cost_record = {
                "amount": amount,
                "provider": provider,
                "model": model,
                "agent_id": agent_id,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "request_type": request_type,
                "timestamp": datetime.utcnow()
            }
            
            self._costs.append(cost_record)
            
            today = datetime.utcnow().strftime("%Y-%m-%d")
            self._daily_costs[today] += amount
            self._provider_costs[provider] += amount
            self._agent_costs[agent_id] += amount
            self._model_costs[model] += amount
            
            self._request_count += 1
            self._token_count += tokens_in + tokens_out
            
            if self.daily_budget:
                daily_total = self._daily_costs[today]
                if daily_total >= self.daily_budget * self.alert_threshold:
                    if not self._alert_sent_today:
                        await self._send_budget_alert(daily_total)
                        self._alert_sent_today = True
    
    async def _send_budget_alert(self, current_cost: float):
        
        print(f"⚠️ BUDGET ALERT: Daily cost ${current_cost:.4f} "
              f"exceeds {self.alert_threshold*100}% of budget ${self.daily_budget:.4f}")
    
    async def get_daily_cost(self, date: Optional[datetime] = None) -> float:
        
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y-%m-%d")
        return self._daily_costs.get(date_str, 0.0)
    
    async def get_current_period_cost(self, days: int = 1) -> float:
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        total = 0.0
        for cost in self._costs:
            if cost["timestamp"] >= cutoff:
                total += cost["amount"]
        
        return total
    
    async def generate_report(self, 
                             days: int = 7,
                             agent_id: Optional[str] = None) -> CostReport:
        
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            filtered = [
                c for c in self._costs
                if c["timestamp"] >= cutoff
                and (agent_id is None or c["agent_id"] == agent_id)
            ]
            
            total_cost = sum(c["amount"] for c in filtered)
            request_count = len(filtered)
            token_count = sum(c["tokens_in"] + c["tokens_out"] for c in filtered)
            
            by_provider = defaultdict(float)
            by_agent = defaultdict(float)
            by_model = defaultdict(float)
            
            for c in filtered:
                by_provider[c["provider"]] += c["amount"]
                by_agent[c["agent_id"]] += c["amount"]
                by_model[c["model"]] += c["amount"]
            
            return CostReport(
                total_cost=round(total_cost, 4),
                period=f"last_{days}_days",
                by_provider=dict(by_provider),
                by_agent=dict(by_agent),
                by_model=dict(by_model),
                request_count=request_count,
                token_count=token_count,
                start_time=cutoff,
                end_time=datetime.utcnow()
            )
    
    async def get_top_costs(self, 
                           by: str = "agent",
                           limit: int = 10) -> List[Dict[str, Any]]:
        
        async with self._lock:
            if by == "agent":
                costs = self._agent_costs
            elif by == "provider":
                costs = self._provider_costs
            elif by == "model":
                costs = self._model_costs
            else:
                return []
            
            sorted_costs = sorted(
                costs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [
                {"id": k, "cost": round(v, 4)}
                for k, v in sorted_costs
            ]
    
    async def reset_daily_counter(self):
        
        self._alert_sent_today = False
    
    def get_stats(self) -> Dict[str, Any]:
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        return {
            "daily_budget": self.daily_budget,
            "today_cost": round(self._daily_costs.get(today, 0.0), 4),
            "total_requests": self._request_count,
            "total_tokens": self._token_count,
            "by_provider": dict(self._provider_costs),
            "by_model": dict(self._model_costs)
        }

_cost_tracker: Optional[CostTracker] = None

async def get_cost_tracker() -> CostTracker:
    
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker