from backend.graph.vectorstore import get_vectorstore

from backend.core.logging import get_logger
logger = get_logger(__name__)

def get_retriever():
    vectorstore = get_vectorstore()

    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": 2}
    )
    return retriever