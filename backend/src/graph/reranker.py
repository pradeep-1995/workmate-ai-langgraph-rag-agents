from functools import lru_cache

from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

from backend.core.config import settings

from backend.core.logging import get_logger
logger = get_logger(__name__)


@lru_cache
def get_reranker() -> CrossEncoder:
    """
    Create and cache a CrossEncoder reranker instance using 
    the configured model name.
    """

    logger.info(
        "Initialization of reranker with model: %s",
        settings.reranker_model
    )
    
    return CrossEncoder(settings.reranker_model)


def reranker_documents(query: str, 
                       documents: list[Document], 
                       top_k: int = 3) -> list[Document]:

    """
    Reranker retrieved documents using a CrossEncoder.
    Args:
        query: User's search query.
        documents: Candidate documents
        top_k: Numberof documents to return after reranking.

    Returns:
        Reranked documents.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty or whitespace.")

    if not documents:
        logger.warning("No documents provided for reranking.")
        return []

    if top_k < 1:
        raise ValueError("top_k must be greater than 0.")

    reranker = get_reranker()

    pairs = [(query, doc.page_content) for doc in documents]

    results = reranker.predict(pairs)

    ranked_docs = sorted(
        zip(documents, results), 
        key=lambda x: x[1], 
        reverse=True
    )

    results = []

    for doc, score in ranked_docs[:top_k]:

        # Copy the document and add the reranking score to its metadata
        # Document metadata
        doc.metadata = {**doc.metadata, 
                        "rerank_score": float(score)}

        results.append(doc)

    logger.info(
        "Documents reranked | input = %d | output = %d ",
        len(documents),
        len(results)
    )

    return results

    