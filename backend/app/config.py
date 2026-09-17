"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "KubeRCA Agent"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Environment
    DEBUG: bool = False
    MOCK_MODE: bool = True
    DEFAULT_NAMESPACE: str = "default"
    
    # Security Sandbox
    ENABLE_SECURITY_SANDBOX: bool = True
    MAX_QUERY_LIMIT: int = 100
    MAX_INVESTIGATION_STEPS: int = 12
    EVIDENCE_CONFIDENCE_THRESHOLD: float = 85.0
    
    # LLM Configuration
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    
    # Observability Endpoints (Real Cluster)
    KUBECONFIG_PATH: Optional[str] = None
    PROMETHEUS_URL: str = "http://localhost:9090"
    LOKI_URL: str = "http://localhost:3100"
    JAEGER_URL: str = "http://localhost:16686"
    
    # Storage
    DB_PATH: str = "investigations.sqlite3"


settings = Settings()
