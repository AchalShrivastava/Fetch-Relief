from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "local"
    DEBUG: bool = True

    # Backend
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    # Fetch.ai uAgent
    AGENT_NAME: str = "reliefmesh_coordinator"
    AGENT_PORT: int = 8001
    AGENT_SEED: str = "reliefmesh_coordinator_hackathon_demo_seed_phrase_2026"
    AGENT_ENDPOINT: str = "http://127.0.0.1:8001/submit"

    # Agentverse Mailbox
    AGENT_MAILBOX_KEY: Optional[str] = None
    AGENTVERSE_API_KEY: Optional[str] = None

    # ASI:One API
    ASI_ONE_API_KEY: Optional[str] = None
    ASI1_MODEL: str = "asi1-mini"
    ASI1_BASE_URL: str = "https://api.asi1.ai/v1"

    # Storage
    STORAGE_BACKEND: str = "json"  # "json", "sqlite", or "redis"
    REDIS_URL: Optional[str] = None
    LOCAL_DB_PATH: str = "data/local_store.json"

settings = Settings()
