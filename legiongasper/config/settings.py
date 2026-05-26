import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    framework_name: str = "LEGIONGASPER"
    framework_version: str = "1.0.0"
    edition: str = "OpenClaw Factory"
    
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    
    default_llm_provider: str = "openai"
    default_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"
    
    redis_url: str = "redis://localhost:6379/0"
    chroma_db_path: str = "./data/chroma_db"
    vector_collection_name: str = "legiongasper_memory"
    
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8081
    gateway_workers: int = 1
    
    max_agents: int = 100
    agent_pool_size: int = 10
    agent_timeout: int = 300
    
    max_squad_size: int = 10
    parallel_executions: int = 5
    
    enable_audit_logging: bool = True
    enable_cost_tracking: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    dashboard_title: str = "LEGIONGASPER Command Center"
    refresh_interval: int = 5
    
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings() -> Settings:
    
    global _settings
    _settings = Settings()
    return _settings