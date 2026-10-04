from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "WorkMate AI"
    app_env: str = "production"
    debug: bool = False


    model_name: str
    api_key: SecretStr
    environment: str = "production"
    log_level: str = "info"



    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8")



@lru_cache()
def get_settings() -> Settings:
    """Get the application settings, cached for performance."""
    return Settings()


settings = get_settings()