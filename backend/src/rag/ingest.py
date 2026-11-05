# backend/src/rag/ingest.py

from backend.src.rag.loader import load_pdf
from backend.src.rag.chunker import chunk_documents
from backend.src.rag.vectorstore import add_documents
from backend.core.logging import get_logger


logger = get_logger(__name__)

PDF_PATH = "backend/data/WorkMate_AI_Productivity_Knowledge_Base.pdf"

def ingest_pdf(pdf_path: str = PDF_PATH) -> int:
    """
    Ingest a PDF file into the vector store.
    
    Args:
        pdf_path: Path to the PDF file to ingest.
    Returns:
        int: The number of documents ingested.
    """
    documents = load_pdf(pdf_path)
    chunks = chunk_documents(documents)
    ids = add_documents(chunks)

    logger.info(
        "PDF ingestion completed | chunks=%d | ids=%d",
        len(chunks),
        len(ids),
    )

    return len(ids)


if __name__ == "__main__":
    ingest_pdf()