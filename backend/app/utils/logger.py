import logging
import sys
from typing import Optional


def _default_formatter() -> logging.Formatter:
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    return logging.Formatter(fmt)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name or "pixelcraft")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_default_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
