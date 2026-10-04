from functools import lru_cache

from langchain_groq import ChatGroq

from core.config import get_settings

@lru_cache
def get_llm() -> ChatGroq:
    s = get_settings()
    return ChatGroq(
        model = s.model_name,
        api_key = s.api_key,
        temperature = 0.1,
        max_tokens = 100,
    )