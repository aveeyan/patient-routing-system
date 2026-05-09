# core/logger.py

"""Logger configuration for the system"""

# Standard Imports
import sys

# Third Party Imports
from loguru import logger

# Local Imports
from core.config import settings


## Log Format
_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

_STDERR_LEVELS = {"WARNING", "ERROR", "CRITICAL"}


def setup_logger() -> None:
    """Configure loguru logger for the application.

    Removes the default handler and adds:
    - stdout handler: INFO and below, colored, filtered to non-error levels
    - stderr handler: WARNING and above, colored
    - optional file handler: all levels, written to settings.log_file if configured
    """
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=_LOG_FORMAT,
        colorize=True,
        filter=lambda record: record["level"].name not in _STDERR_LEVELS,
    )

    logger.add(
        sys.stderr,
        level="WARNING",
        format=_LOG_FORMAT,
        colorize=True,
    )

    if settings.log_file:
        logger.add(
            settings.log_file,
            level=settings.log_level,
            format=_LOG_FORMAT,
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            colorize=False,
        )
        logger.info("File logging enabled", path=settings.log_file)


setup_logger()
