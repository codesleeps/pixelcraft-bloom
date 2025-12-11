import logging
import sys
import json
from typing import Optional, Any, Dict
from datetime import datetime
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from pythonjsonlogger import jsonlogger

# Context variable for correlation ID
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
            
        # Add correlation ID
        correlation_id = correlation_id_ctx.get()
        if correlation_id:
            log_record['correlation_id'] = correlation_id
            
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

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

class AuditLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def log_event(self, event_type: str, user_id: Optional[str], details: Dict[str, Any], status: str = "success"):
        """Log a security or business critical event."""
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "status": status,
            "details": details,
            "audit": True
        }
        self.logger.info(f"Audit: {event_type}", extra=log_data)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name or "agentsflowai")
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console Handler (JSON)
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler (Rotating)
        log_dir = "/var/log/agentsflowai"
        # Ensure log directory exists or fallback to /tmp if permission denied (for dev)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError:
                log_dir = "/tmp/agentsflowai_logs"
                os.makedirs(log_dir, exist_ok=True)
                
        file_handler = RotatingFileHandler(
            filename=f"{log_dir}/app.log",
            maxBytes=10 * 1024 * 1024, # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Check if Sentry is initialized and add custom handler if active
    try:
        if sentry_sdk.get_global_scope().client is not None:
            # Avoid adding multiple sentry handlers
            if not any(isinstance(h, SentryHandler) for h in logger.handlers):
                sentry_handler = SentryHandler()
                sentry_handler.setFormatter(CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s'))
                logger.addHandler(sentry_handler)
    except Exception:
        pass  # Gracefully handle if Sentry is not available or initialized
    
    return logger

# Global audit logger instance
audit_logger = AuditLogger(get_logger("agentsflowai.audit"))

# Global default logger instance
logger = get_logger()

def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    try:
        with sentry_sdk.configure_scope() as scope:
            for k, v in context.items():
                scope.set_context(k, v)
            logger.log(level, message, extra=context)
    except Exception:
        logger.log(level, message, extra=context)

def capture_exception_with_context(exception: Exception, **context):
    try:
        with sentry_sdk.configure_scope() as scope:
            for k, v in context.items():
                scope.set_context(k, v)
            sentry_sdk.capture_exception(exception)
    except Exception:
        pass
