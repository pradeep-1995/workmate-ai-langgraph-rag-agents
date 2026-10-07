from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.src.graph.embeddings import get_embeddings

from backend.core.logging import get_logger
logger = get_logger(__name__)


@lru_cache
def get_vectorstore() -> Chroma:
    """
    Create and return a Chroma vector store instance using 
    the configured embeddings.

    Returns:
        Chroma: An instance of Chroma vector store.
    """
    embeddings = get_embeddings()

    vectorstore = Chroma(
        collection_name="workmate_ai",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

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

    ids = vectorstore.add_documents(documents)

    logger.info(
        "Documents added to Chroma | count=%d", len(ids))

    return ids