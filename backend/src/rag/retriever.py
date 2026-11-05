#from langchain_core.retrievers import BaseRetriever
from backend.src.rag.vectorstore import get_vectorstore


from backend.core.logging import get_logger
logger = get_logger(__name__)


def get_retriever():
    """
    Return a simple retriever function backed by Chroma.
    """
    vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": 3},
    )

    logger.info("Chroma retiever intialized | k=3")
    return retriever