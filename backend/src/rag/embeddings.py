from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

@lru_cache
def get_embeddings():
    """
    Create and return a cached HuggingFace MiniLM embeddings instance.
    
    Returns:
        HuggingFaceEmbeddings: An instance of HuggingFaceEmbeddings for MiniLM.
    """
    model_name = settings.huggingface_model_name

    logger.info("Initializing HuggingFace embeddings with model: %s", model_name)

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        }
    )