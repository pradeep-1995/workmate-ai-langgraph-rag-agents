from functools import lru_cache
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.src.rag.embeddings import get_embeddings
from backend.core.logging import get_logger

logger = get_logger(__name__)

CHROMA_DIR = Path(__file__).resolve().parents[3] / "data" / "chroma_db"

@lru_cache
def get_vectorstore() -> Chroma:
    """
    Create and return a Chroma vector store instance using 
    the configured embeddings.

    Returns:
        Chroma: An instance of Chroma vector store.
    """

    embeddings = get_embeddings()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    vectorstore = Chroma(
        collection_name = "workmate_rag",
        embedding_function = embeddings,
        persist_directory = str(CHROMA_DIR),
    )

    logger.info("Chroma vector store initialized at: %s", CHROMA_DIR)
    
    return vectorstore



def add_documents(documents: list[Document]) -> list[str]:
    """
    Add documents to the Chroma vector store.

    Args:
        documents (list[Document]): A list of Document objects to add.

    Returns:
        list[str]: A list of IDs for the added documents.
    """
    if not documents:
        logger.warning("No documents to add to the vector store.")
        return []

    vectorstore = get_vectorstore()

    all_ids = []

    for start in range(0, len(documents), 25):
        batch = documents[start:start + 25]

        ids = vectorstore.add_documents(batch)
        all_ids.extend(ids)

    logger.info("Added documents to Chroma | batch=%d | total=%d",
                len(batch),
                len(all_ids))



    return all_ids

