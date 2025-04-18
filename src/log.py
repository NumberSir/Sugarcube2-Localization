"""Output infos during running."""
import sys

from loguru import logger as logger_

from src.config import settings

logger_.remove()
logger_.add(sys.stdout, format=settings.project.log_format, colorize=True)

logger = logger_

__all__ = ["logger"]
