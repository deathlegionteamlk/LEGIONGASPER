import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum

class DecompositionStrategy(str, Enum):
    
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    MAP_REDUCE = "map_reduce"

class AggregationStrategy(str, Enum):
    
    CONCATENATE = "concatenate"
    SUMMARIZE = "summarize"
    VOTE = "vote"
    MERGE = "merge"
    PRIORITY = "priority"

class SquadFormation(BaseModel):
    
    min_agents: int = 2
    max_agents: int = 5
    required_roles: List[str] = []
    preferred_templates: List[str] = []
    diversity_weight: float = 0.5

class CaptainRole(BaseModel):
    
    role_id: str
    name: str
    description: str
    
    decomposition_strategy: DecompositionStrategy = DecompositionStrategy.HYBRID
    aggregation_strategy: AggregationStrategy = AggregationStrategy.SUMMARIZE
    
    squad_formation: SquadFormation = Field(default_factory=SquadFormation)
    
    llm_provider: str = "openai"
    model_tier: str = "premium"
    temperature: float = 0.3  
    
    planning_prompt: str = ""
    aggregation_prompt: str = ""
    
    can_delegate: bool = True
    can_replan: bool = True
    max_replanning_attempts: int = 3
    
    tags: List[str] = []
    version: str = "1.0"
    
    class Config:
        extra = "allow"

class CaptainRoleRegistry:
    
    def __init__(self, config_path: Optional[str] = None):
        self.roles: Dict[str, CaptainRole] = {}
        self.config_path = config_path or "./configs/captain_roles.yaml"
        self._load_roles()
    
    def _load_roles(self):
        
        path = Path(self.config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data and 'roles' in data:
                    for role_data in data['roles']:
                        role = CaptainRole(**role_data)
                        self.roles[role.role_id] = role
        else:
            self._load_defaults()
    
    def _load_defaults(self):
        
        defaults = [
            CaptainRole(
                role_id="research_captain",
                name="Research Captain",
                description="Orchestrates research tasks with parallel information gathering",
                decomposition_strategy=DecompositionStrategy.PARALLEL,
                aggregation_strategy=AggregationStrategy.SUMMARIZE,
                squad_formation=SquadFormation(
                    min_agents=2,
                    max_agents=5,
                    required_roles=["researcher"],
                    preferred_templates=["researcher", "analyst"],
                    diversity_weight=0.3
                ),
                tags=["research", "information"]
            ),
            CaptainRole(
                role_id="code_captain",
                name="Code Review Captain",
                description="Orchestrates code review with multi-angle analysis",
                decomposition_strategy=DecompositionStrategy.PARALLEL,
                aggregation_strategy=AggregationStrategy.MERGE,
                squad_formation=SquadFormation(
                    min_agents=2,
                    max_agents=4,
                    required_roles=["reviewer", "coder"],
                    preferred_templates=["reviewer", "coder", "analyst"],
                    diversity_weight=0.4
                ),
                tags=["code", "review", "quality"]
            ),
            CaptainRole(
                role_id="content_captain",
                name="Content Creation Captain",
                description="Orchestrates content creation with iterative refinement",
                decomposition_strategy=DecompositionStrategy.SEQUENTIAL,
                aggregation_strategy=AggregationStrategy.CONCATENATE,
                squad_formation=SquadFormation(
                    min_agents=2,
                    max_agents=3,
                    required_roles=["writer"],
                    preferred_templates=["writer", "reviewer"],
                    diversity_weight=0.2
                ),
                tags=["content", "writing"]
            ),
            CaptainRole(
                role_id="analysis_captain",
                name="Data Analysis Captain",
                description="Orchestrates complex data analysis with multi-stage processing",
                decomposition_strategy=DecompositionStrategy.HYBRID,
                aggregation_strategy=AggregationStrategy.SUMMARIZE,
                squad_formation=SquadFormation(
                    min_agents=2,
                    max_agents=4,
                    required_roles=["analyst"],
                    preferred_templates=["analyst", "researcher"],
                    diversity_weight=0.5
                ),
                tags=["analysis", "data"]
            ),
            CaptainRole(
                role_id="general_captain",
                name="General Purpose Captain",
                description="General purpose captain for mixed tasks",
                decomposition_strategy=DecompositionStrategy.HYBRID,
                aggregation_strategy=AggregationStrategy.SUMMARIZE,
                squad_formation=SquadFormation(
                    min_agents=2,
                    max_agents=5,
                    required_roles=[],
                    preferred_templates=["researcher", "analyst", "writer"],
                    diversity_weight=0.6
                ),
                tags=["general", "multi-purpose"]
            ),
        ]
        for role in defaults:
            self.roles[role.role_id] = role
    
    def get_role(self, role_id: str) -> Optional[CaptainRole]:
        
        return self.roles.get(role_id)
    
    def list_roles(self) -> List[CaptainRole]:
        
        return list(self.roles.values())
    
    def register_role(self, role: CaptainRole):
        
        self.roles[role.role_id] = role
    
    def get_by_tags(self, tags: List[str]) -> List[CaptainRole]:
        
        return [r for r in self.roles.values() if any(t in r.tags for t in tags)]
    
    def save_to_file(self, path: Optional[str] = None):
        
        save_path = Path(path or self.config_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "roles": [r.model_dump() for r in self.roles.values()]
        }
        
        with open(save_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

_role_registry: Optional[CaptainRoleRegistry] = None

def get_role_registry() -> CaptainRoleRegistry:
    
    global _role_registry
    if _role_registry is None:
        _role_registry = CaptainRoleRegistry()
    return _role_registry