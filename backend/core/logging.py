import logging
import sys

def setup_logging() -> None:
    """
    configures the logging settings for the application.
    """

    logging.basicConfig(
        level = logging.INFO,
        format = (
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers = [
            logging.StreamHandler(sys.stdout),
        ],
        force = True,
    )

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)
