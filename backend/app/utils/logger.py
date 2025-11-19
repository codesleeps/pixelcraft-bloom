import logging
import sys
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


class CustomFormatter(logging.Formatter):
    def format(self, record):
        fmt = "%(asctime)s %(levelname)s %(name)s"
        if hasattr(record, 'correlation_id') and record.correlation_id:
            fmt += " [%(correlation_id)s]"
        fmt += " %(message)s"
        self._fmt = fmt
        return super().format(record)


class DuplicateFilter(logging.Filter):
    def filter(self, record):
        # Prevent duplicate error reporting by filtering out logs from Sentry-related sources
        return 'sentry' not in record.name.lower()


class SentryHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.addFilter(DuplicateFilter())
    
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            sentry_sdk.capture_message(self.format(record), level=record.levelname.lower())


def _default_formatter() -> logging.Formatter:
    return CustomFormatter()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name or "pixelcraft")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_default_formatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Check if Sentry is initialized and add custom handler if active
    try:
        if sentry_sdk.get_global_scope().client is not None:
            sentry_handler = SentryHandler()
            sentry_handler.setFormatter(_default_formatter())
            logger.addHandler(sentry_handler)
    except Exception:
        pass  # Gracefully handle if Sentry is not available or initialized
    
    return logger


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    try:
        with sentry_sdk.configure_scope() as scope:
            for k, v in context.items():
                scope.set_context(k, v)
            logger.log(level, message)
    except Exception:
        logger.log(level, message)


def capture_exception_with_context(exception: Exception, **context):
    try:
        with sentry_sdk.configure_scope() as scope:
            for k, v in context.items():
                scope.set_context(k, v)
            sentry_sdk.capture_exception(exception)
    except Exception:
        pass
