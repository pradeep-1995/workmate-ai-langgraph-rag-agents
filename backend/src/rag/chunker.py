from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.logging import get_logger
logger = get_logger(__name__)

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 800,
    chunk_overlap = 120,
    separators = ["\n\n", "\n", " ", ""],)

def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split LangChain Document into smaller chunks.
    Args:
        documents: Documents returned by the document loader.
        
    Returns:
        A list of chunked LangChain Documents.
    """

    if not documents:
        logger.warning("No documents to chunk.")
        return []

    logger.info(
        "Starting document chunking | documents=%d",
        len(documents),
    )

    chunks = splitter.split_documents(documents)

    logger.info(
        "Document chunking completed | chunks=%d",
        len(chunks),
    )

    return chunks