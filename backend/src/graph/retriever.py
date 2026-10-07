from langchain_core.retrievers import BaseRetriever
from backend.src.graph.vectorstore import get_vectorstore


from backend.core.logging import get_logger
logger = get_logger(__name__)


def get_retriever() -> BaseRetriever:
    """
    Return the Chroma similarity retriever instance.
    """

    vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": 4}
    )

    logger.info("Chroma retriever initialized | k=%d", 4)

    return retriever