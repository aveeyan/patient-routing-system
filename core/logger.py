# core/logger.py

"""Logger configuration for the system"""

# Standard Imports
import sys

# Third Party Imports
from loguru import logger

# Local Imports
from core.config import settings

def setup_logger() -> None:
    """
    Configure loguru logger for the application.

    Removes the default handler and adds a custom one with:
    - Structured format with timestamps, levels, and source location
    - Log level from application settings
    - Colored output for terminal readability
    - Proper routing: INFO and below to stdout, WARNING and above to stderr
    """

    # Remove the default loguru handler
    logger.remove()

    # Add a custom handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        filter=lambda record: record["level"].no < 40
    )

    # WARNING and ERROR go to stderr
    logger.add(
        sys.stderr,
        level="WARNING",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )


# Initialize on import
setup_logger()
