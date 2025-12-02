import logging
import sys
from datetime import datetime
from functools import lru_cache

from aiologger import Logger
from aiologger.formatters.base import Formatter
from aiologger.handlers.streams import AsyncStreamHandler


class CustomFormatter(Formatter):
    """Custom formatter with datetime, module, and line number"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with datetime, module, and line number."""
        # Format: YYYY-MM-DD HH:MM:SS | MODULE | LINE | LEVEL | MESSAGE
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        module = record.module or "unknown"
        line = record.lineno or 0
        level = record.levelname
        message = record.getMessage()

        return f"{timestamp} | {module} | {line} | {level} | {message}"


def setup_logger(name: str = "crypto_collector") -> Logger:
    """Setup and return configured logger"""
    logger = Logger(name=name)

    formatter = CustomFormatter()
    handler = AsyncStreamHandler(stream=sys.stdout)
    handler.formatter = formatter

    logger.add_handler(handler)
    return logger


@lru_cache
def get_logger() -> Logger:
    """Return cached logger instance so we do not re-create it repeatedly."""
    return setup_logger()
