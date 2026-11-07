from functools import lru_cache

from langchain_openrouter import ChatOpenRouter

from backend.core.config import settings

@lru_cache
def get_llm() -> ChatOpenRouter:
    """
    Create and cache the WorkMate AI Chat model.
    
    Returns:
        Configured ChatOpenRouter instance.
    """
    

    return ChatOpenRouter(
        model = settings.openrouter_model_name,
        api_key = settings.openrouter_api_key.get_secret_value(),
        temperature = 0.1,
        max_tokens = 1024,
        max_retries = 3,
    )

