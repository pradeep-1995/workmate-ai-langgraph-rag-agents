from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr
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
    huggingface_api_key: SecretStr = Field(
        validation_alias=AliasChoices(
            "HUGGINGFACE_API_KEY",
            "HUGGINGFACEHUB_API_TOKEN",
        )
    )

    # Reranker
    reranker_model: str = "cross-encoder/ms-macro-MiniLM-L-6-v2"

    # Runtime
    environment: str = "production"
    log_level: str = "info"

    # Google OAuth credentials
    google_cloud_project_id: str
    google_client_id: str
    google_client_secret: SecretStr

    # Google MCP endpoints
    gmail_mcp_url: str = "https://gmailmcp.googleapis.com/mcp/v1"
    google_calendar_mcp_url: str = "https://calendarmcp.googleapis.com/mcp/v1"

    # OAuth callback configured in your FastAPI application
    google_oauth_redirect_url: str = "https://localhost:8000/auth/google/callback"

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