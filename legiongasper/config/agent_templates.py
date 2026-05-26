import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field

class AgentCapability(BaseModel):
    
    name: str
    description: str
    tools: List[str] = []
    permissions: List[str] = []

class AgentTemplate(BaseModel):
    
    template_id: str
    name: str
    description: str
    role: str
    
    llm_provider: str = "openai"
    model_tier: str = "standard"  
    temperature: float = 0.7
    max_tokens: int = 2000
    
    capabilities: List[AgentCapability] = []
    allowed_tools: List[str] = []
    
    system_prompt: str = ""
    response_format: str = "text"  
    
    max_memory_items: int = 1000
    timeout_seconds: int = 300
    
    tags: List[str] = []
    version: str = "1.0"
    
    class Config:
        extra = "allow"

class AgentTemplateRegistry:
    
    def __init__(self, config_path: Optional[str] = None):
        self.templates: Dict[str, AgentTemplate] = {}
        self.config_path = config_path or "./configs/agent_templates.yaml"
        self._load_templates()
    
    def _load_templates(self):
        
        path = Path(self.config_path)
        if path.exists():
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if data and 'templates' in data:
                    for template_data in data['templates']:
                        template = AgentTemplate(**template_data)
                        self.templates[template.template_id] = template
        else:
            
            self._load_defaults()
    
    def _load_defaults(self):
        
        defaults = [
            AgentTemplate(
                template_id="researcher",
                name="Research Agent",
                description="Specialized in web research and information gathering",
                role="researcher",
                llm_provider="openai",
                model_tier="standard",
                allowed_tools=["web_search", "web_scrape", "summarize"],
                system_prompt="You are a research specialist. Gather accurate information efficiently.",
                tags=["research", "information"]
            ),
            AgentTemplate(
                template_id="coder",
                name="Code Agent",
                description="Specialized in code generation and review",
                role="coder",
                llm_provider="anthropic",
                model_tier="premium",
                allowed_tools=["code_execution", "file_operations", "syntax_check"],
                system_prompt="You are a code specialist. Write clean, efficient, well-documented code.",
                tags=["coding", "development"]
            ),
            AgentTemplate(
                template_id="analyst",
                name="Analysis Agent",
                description="Specialized in data analysis and insights",
                role="analyst",
                llm_provider="openai",
                model_tier="standard",
                allowed_tools=["data_query", "chart_generation", "calculator"],
                system_prompt="You are an analysis specialist. Extract meaningful insights from data.",
                tags=["analysis", "data"]
            ),
            AgentTemplate(
                template_id="writer",
                name="Content Agent",
                description="Specialized in content creation and editing",
                role="writer",
                llm_provider="openai",
                model_tier="economy",
                allowed_tools=["file_operations", "grammar_check", "summarize"],
                system_prompt="You are a content specialist. Create engaging, clear content.",
                tags=["writing", "content"]
            ),
            AgentTemplate(
                template_id="reviewer",
                name="Review Agent",
                description="Specialized in code and content review",
                role="reviewer",
                llm_provider="anthropic",
                model_tier="premium",
                allowed_tools=["syntax_check", "compare_text", "file_operations"],
                system_prompt="You are a review specialist. Provide thorough, constructive feedback.",
                tags=["review", "quality"]
            ),
        ]
        for template in defaults:
            self.templates[template.template_id] = template
    
    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[AgentTemplate]:
        
        return list(self.templates.values())
    
    def register_template(self, template: AgentTemplate):
        
        self.templates[template.template_id] = template
    
    def get_by_role(self, role: str) -> List[AgentTemplate]:
        
        return [t for t in self.templates.values() if t.role == role]
    
    def save_to_file(self, path: Optional[str] = None):
        
        save_path = Path(path or self.config_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "templates": [t.model_dump() for t in self.templates.values()]
        }
        
        with open(save_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

_registry: Optional[AgentTemplateRegistry] = None

def get_template_registry() -> AgentTemplateRegistry:
    
    global _registry
    if _registry is None:
        _registry = AgentTemplateRegistry()
    return _registry