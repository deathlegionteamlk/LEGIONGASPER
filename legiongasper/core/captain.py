import asyncio
import uuid
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import json
import logging

from .agent import Agent
from .squad import Squad
from .factory import get_agent_factory
from ..config import CaptainRole, get_role_registry
from ..llm import get_llm_router, Message

@dataclass
class Subtask:
    
    subtask_id: str
    description: str
    assigned_agent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  
    result: Any = None
    priority: int = 1

@dataclass
class DecompositionPlan:
    
    plan_id: str
    original_task: str
    subtasks: List[Subtask]
    strategy: str
    estimated_steps: int

@dataclass
class AggregationResult:
    
    success: bool
    result: Any
    contributions: Dict[str, Any]
    metadata: Dict[str, Any]

class Captain:
    
    def __init__(self, 
                 role: CaptainRole,
                 captain_id: Optional[str] = None):
        
        self.captain_id = captain_id or f"captain_{uuid.uuid4().hex[:8]}"
        self.role = role
        
        self.active_squads: Dict[str, Squad] = {}
        self.completed_tasks: List[str] = []
        
        self.active_plans: Dict[str, DecompositionPlan] = {}
        
        self._factory = None
        self._llm_router = None
        
        self._logger = logging.getLogger(f"{__name__}.{self.captain_id}")
    
    async def _ensure_dependencies(self):
        
        if self._factory is None:
            self._factory = await get_agent_factory()
        if self._llm_router is None:
            self._llm_router = await get_llm_router()
    
    async def orchestrate(self, 
                         task: str,
                         context: Optional[Dict] = None,
                         custom_squad: Optional[Squad] = None) -> AggregationResult:
        
        await self._ensure_dependencies()
        
        self._logger.info(f"Captain {self.captain_id} orchestrating task: {task[:100]}...")
        
        plan = await self._decompose_task(task, context)
        self.active_plans[plan.plan_id] = plan
        
        if custom_squad:
            squad = custom_squad
        else:
            squad = await self._form_squad(plan, context)
        
        self.active_squads[squad.squad_id] = squad
        
        results = await self._execute_plan(plan, squad, context)
        
        aggregated = await self._aggregate_results(plan, results)
        
        self.completed_tasks.append(plan.plan_id)
        
        return aggregated
    
    async def _decompose_task(self, 
                             task: str, 
                             context: Optional[Dict]) -> DecompositionPlan:
        
        self._logger.info(f"Decomposing task using {self.role.decomposition_strategy.value} strategy")
        
        messages = [
            Message(role="system", content=self.role.planning_prompt),
            Message(role="user", content=f)
        ]
        
        try:
            response = await self._llm_router.complete(
                messages=messages,
                tier=self.role.model_tier,
                temperature=self.role.temperature
            )
            
            import json
            try:
                decomposition = json.loads(response.content)
            except json.JSONDecodeError:
                
                decomposition = {
                    "subtasks": [{"description": task, "priority": 1, "dependencies": []}],
                    "estimated_steps": 1
                }
            
            subtasks = []
            for i, st_data in enumerate(decomposition.get("subtasks", [])):
                subtask = Subtask(
                    subtask_id=f"subtask_{uuid.uuid4().hex[:8]}",
                    description=st_data.get("description", ""),
                    priority=st_data.get("priority", 1),
                    dependencies=st_data.get("dependencies", [])
                )
                subtasks.append(subtask)
            
            plan = DecompositionPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                original_task=task,
                subtasks=subtasks,
                strategy=self.role.decomposition_strategy.value,
                estimated_steps=decomposition.get("estimated_steps", len(subtasks))
            )
            
            self._logger.info(f"Created plan with {len(subtasks)} subtasks")
            return plan
            
        except Exception as e:
            self._logger.error(f"Decomposition failed: {e}")
            
            return DecompositionPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                original_task=task,
                subtasks=[Subtask(
                    subtask_id=f"subtask_{uuid.uuid4().hex[:8]}",
                    description=task,
                    priority=1
                )],
                strategy="simple",
                estimated_steps=1
            )
    
    async def _form_squad(self, 
                         plan: DecompositionPlan,
                         context: Optional[Dict]) -> Squad:
        
        formation = self.role.squad_formation
        
        self._logger.info(f"Forming squad: {formation.min_agents}-{formation.max_agents} agents")
        
        template_ids = []
        
        for role in formation.required_roles:
            templates = self._factory.template_registry.get_by_role(role)
            if templates:
                template_ids.append(templates[0].template_id)
        
        for template_id in formation.preferred_templates:
            if template_id not in template_ids:
                template_ids.append(template_id)
        
        while len(template_ids) < formation.min_agents:
            
            template_ids.append("researcher")
        
        template_ids = template_ids[:formation.max_agents]
        
        squad = Squad(
            captain_id=self.captain_id,
            template_ids=template_ids
        )
        
        await squad.initialize()
        
        self._logger.info(f"Squad {squad.squad_id} formed with {len(squad.agents)} agents")
        return squad
    
    async def _execute_plan(self,
                           plan: DecompositionPlan,
                           squad: Squad,
                           context: Optional[Dict]) -> Dict[str, Any]:
        
        results = {}
        
        if self.role.decomposition_strategy.value == "sequential":
            
            for subtask in plan.subtasks:
                result = await self._execute_subtask(subtask, squad, context)
                results[subtask.subtask_id] = result
                subtask.status = "completed" if result.get("success") else "failed"
                subtask.result = result
                
        elif self.role.decomposition_strategy.value == "parallel":
            
            tasks = [
                self._execute_subtask(st, squad, context)
                for st in plan.subtasks
            ]
            subtask_results = await asyncio.gather(*tasks)
            
            for subtask, result in zip(plan.subtasks, subtask_results):
                results[subtask.subtask_id] = result
                subtask.status = "completed" if result.get("success") else "failed"
                subtask.result = result
                
        else:  
            
            results = await self._execute_with_dependencies(plan, squad, context)
        
        return results
    
    async def _execute_subtask(self,
                              subtask: Subtask,
                              squad: Squad,
                              context: Optional[Dict]) -> Dict[str, Any]:
        
        agent = await squad.get_available_agent()
        if not agent:
            return {"success": False, "error": "No available agents"}
        
        subtask.assigned_agent_id = agent.agent_id
        subtask.status = "assigned"
        
        result = await agent.execute(subtask.description, context)
        
        await squad.release_agent(agent.agent_id)
        
        return result
    
    async def _execute_with_dependencies(self,
                                        plan: DecompositionPlan,
                                        squad: Squad,
                                        context: Optional[Dict]) -> Dict[str, Any]:
        
        results = {}
        completed = set()
        
        while len(completed) < len(plan.subtasks):
            
            ready = [
                st for st in plan.subtasks
                if st.subtask_id not in completed
                and all(dep in completed for dep in st.dependencies)
            ]
            
            if not ready:
                break
            
            tasks = [
                self._execute_subtask(st, squad, context)
                for st in ready
            ]
            subtask_results = await asyncio.gather(*tasks)
            
            for subtask, result in zip(ready, subtask_results):
                results[subtask.subtask_id] = result
                completed.add(subtask.subtask_id)
                subtask.status = "completed" if result.get("success") else "failed"
                subtask.result = result
        
        return results
    
    async def _aggregate_results(self,
                                plan: DecompositionPlan,
                                results: Dict[str, Any]) -> AggregationResult:
        
        self._logger.info(f"Aggregating results using {self.role.aggregation_strategy.value} strategy")
        
        successful = {
            k: v for k, v in results.items()
            if v.get("success", False)
        }
        
        if not successful:
            return AggregationResult(
                success=False,
                result="All subtasks failed",
                contributions=results,
                metadata={"strategy": self.role.aggregation_strategy.value}
            )
        
        if self.role.aggregation_strategy.value == "concatenate":
            aggregated = self._concatenate_results(successful)
        elif self.role.aggregation_strategy.value == "summarize":
            aggregated = await self._summarize_results(successful)
        elif self.role.aggregation_strategy.value == "vote":
            aggregated = self._vote_results(successful)
        elif self.role.aggregation_strategy.value == "merge":
            aggregated = self._merge_results(successful)
        else:
            aggregated = self._concatenate_results(successful)
        
        return AggregationResult(
            success=True,
            result=aggregated,
            contributions=results,
            metadata={
                "strategy": self.role.aggregation_strategy.value,
                "successful_subtasks": len(successful),
                "total_subtasks": len(results)
            }
        )
    
    def _concatenate_results(self, results: Dict[str, Any]) -> str:
        
        parts = []
        for subtask_id, result in results.items():
            content = result.get("result", "")
            parts.append(f"[{subtask_id}]\n{content}")
        return "\n\n".join(parts)
    
    async def _summarize_results(self, results: Dict[str, Any]) -> str:
        
        concatenated = self._concatenate_results(results)
        
        messages = [
            Message(role="system", content=self.role.aggregation_prompt),
            Message(role="user", content=f"Summarize the following results:\n\n{concatenated}")
        ]
        
        try:
            response = await self._llm_router.complete(
                messages=messages,
                tier=self.role.model_tier,
                temperature=0.3
            )
            return response.content
        except Exception as e:
            self._logger.error(f"Summarization failed: {e}")
            return concatenated
    
    def _vote_results(self, results: Dict[str, Any]) -> Any:
        
        votes = {}
        for result in results.values():
            content = str(result.get("result", ""))
            votes[content] = votes.get(content, 0) + 1
        
        if votes:
            return max(votes.items(), key=lambda x: x[1])[0]
        return ""
    
    def _merge_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        
        merged = {}
        for result in results.values():
            if isinstance(result.get("result"), dict):
                merged.update(result["result"])
            else:
                merged[result.get("agent_id", "unknown")] = result.get("result")
        return merged
    
    async def replan(self, 
                    plan_id: str,
                    reason: str) -> Optional[DecompositionPlan]:
        
        if not self.role.can_replan:
            return None
        
        old_plan = self.active_plans.get(plan_id)
        if not old_plan:
            return None
        
        self._logger.info(f"Replanning {plan_id}: {reason}")
        
        return await self._decompose_task(
            old_plan.original_task + f"\n\nPrevious attempt failed: {reason}",
            None
        )
    
    def get_status(self) -> Dict[str, Any]:
        
        return {
            "captain_id": self.captain_id,
            "role": self.role.role_id,
            "active_squads": len(self.active_squads),
            "active_plans": len(self.active_plans),
            "completed_tasks": len(self.completed_tasks)
        }
    
    async def terminate(self):
        
        self._logger.info(f"Terminating captain {self.captain_id}")
        
        for squad in self.active_squads.values():
            await squad.terminate()
        
        self.active_squads.clear()

async def create_captain(role_id: str, captain_id: Optional[str] = None) -> Captain:
    
    registry = get_role_registry()
    role = registry.get_role(role_id)
    
    if not role:
        raise ValueError(f"Captain role not found: {role_id}")
    
    return Captain(role=role, captain_id=captain_id)