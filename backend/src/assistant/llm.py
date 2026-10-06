from functools import lru_cache

from langchain_openrouter import ChatOpenRouter

from core.config import get_settings

@lru_cache
def get_llm() -> ChatOpenRouter:
    """
    Create and cache the WorkMate AI Chat model.
    
    Returns:
        Configured ChatOpenRouter instance.
    """
    
    s = get_settings()

    return ChatOpenRouter(
        model = s.openrouter_model_name,
        api_key = s.openrouter_api_key.get_secret_value(),
        temperature = 0.1,
        max_tokens = 100,
        max_retries = 3,
    )

