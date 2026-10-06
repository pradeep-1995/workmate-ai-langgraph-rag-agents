from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings

from backend.core.config import settings

from backend.core.logging import get_logger
logger = get_logger(__name__)

@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Create and return a HuggingFaceEmbeddings instance using the configured model name and API key.
    
    Returns:
        HuggingFaceEmbeddings: An instance of HuggingFaceEmbeddings.
    """
    return HuggingFaceEmbeddings(
        model_name=settings.huggingface_model_name,
        huggingfacehub_api_token=settings.huggingface_api_key.get_secret_value()
    )