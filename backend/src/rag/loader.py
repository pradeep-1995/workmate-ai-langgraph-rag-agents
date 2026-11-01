from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from backend.core.logging import get_logger
logger = get_logger(__name__)


def load_pdf(file_path: str | Path) -> list[Document]:
    """
    Load a PDF file using LangChain's PyPDFLoader.
    
    Args:
        file_path: Path to the PDF file.
        
    Returns:
        A list of LangChain Document objects.
        
    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the file is not a PDF.
        Exception: If PDF loading fails.
    """

    path = Path(file_path)
    logger.info("Starting PDF loading: %s", path)

    if not path.exixts():
        logger.error("PDF file not found: %s", path)
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    if path.suffix.lower() != ".pdf":
        logger.error(
            "Unsupported file type: %s",
            path.suffix
        )
        raise ValueError(
            "Only PDF files are supported."
        )

    try:
        loader = PyPDFLoader(str(path))

        documents = loader.load()

        logger.info(
            "PDF loaded successfully: %s | pages=%d",
            path.name,
            len(documents),
        )
        return documents

    except Exception:
        logger.exception(
            "Failed to load PDF: %s",
            path,
        )
        raise


