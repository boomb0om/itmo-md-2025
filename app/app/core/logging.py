import logging
from functools import lru_cache

from aiologger import Logger
from aiologger.formatters.base import Formatter
from aiologger.handlers.streams import AsyncStreamHandler

from app.core.settings import get_settings

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@lru_cache
def get_logger(name: str) -> Logger:
    """Create a cached async logger configured with app settings."""
    settings = get_settings()
    level = logging.getLevelName(settings.app.log_level.upper())
    logger = Logger(name=name, level=level)
    logger.propagate = False

    formatter = Formatter(fmt=LOG_FORMAT)
    handler = AsyncStreamHandler(formatter=formatter)
    logger.add_handler(handler)
    return logger
