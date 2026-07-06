import logging

from app.core.config import settings


LOG_FORMAT = "%(asctime)s | " "%(levelname)-8s | " "%(name)s | " "%(message)s"


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format=LOG_FORMAT,
)


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger instance.
    """
    return logging.getLogger(name)


logger = get_logger("authforge")
