import logging
import sys

from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# JSON in production for log aggregation, human-readable otherwise
if settings.environment == "production":
    try:
        from pythonjsonlogger import jsonlogger  # optional

        handler = logging.StreamHandler(sys.stdout)
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
        handler.setFormatter(jsonlogger.JsonFormatter(fmt))
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            handlers=[handler],
        )
    except ImportError:
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format=LOG_FORMAT,
            stream=sys.stdout,
        )
else:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=LOG_FORMAT,
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger instance.
    """
    return logging.getLogger(name)


logger = get_logger("authforge")
