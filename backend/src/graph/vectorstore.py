from langchain_chroma import Chroma

from backend.src.graph.embeddings import get_embeddings

from backend.core.logging import get_logger
logger = get_logger(__name__)

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