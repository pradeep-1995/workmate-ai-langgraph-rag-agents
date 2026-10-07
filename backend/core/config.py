from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "WorkMate AI"
    app_env: str = "production"
    debug: bool = False

    # LLM
    openrouter_model_name: str = "openrouter/free"
    openrouter_api_key: SecretStr

    # Embeddings
    huggingface_model_name: str = "all-MiniLM-L6-v2"
    huggingface_api_key: SecretStr

    # Reranker
    reranker_model: str = "cross-encoder/ms-macro-MiniLM-L-6-v2"

    # Runtime
    environment: str = "production"
    log_level: str = "info"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore")



@lru_cache()
def get_settings() -> Settings:
    """Get the application settings, cached for performance."""
    return Settings()


settings = get_settings()