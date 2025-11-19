import sentry_sdk
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import Request


def set_user_context(user_data: Dict[str, Any]) -> None:
    """
    Safely sets user context in Sentry, filtering out sensitive fields like passwords and tokens.

    Args:
        user_data (Dict[str, Any]): A dictionary containing user information.
    """
    try:
        # Filter out sensitive fields
        sensitive_fields = {'password', 'token', 'api_key', 'secret'}
        filtered_user_data = {k: v for k, v in user_data.items() if k not in sensitive_fields}
        sentry_sdk.set_user(filtered_user_data)
    except Exception:
        # Sentry not initialized or other error, silently ignore
        pass


def add_request_context(request: Request) -> None:
    """
    Extracts and sets request context in Sentry (method, URL, headers, query params) while filtering sensitive data.

    Args:
        request (Request): The FastAPI request object.
    """
    try:
        # Filter sensitive headers
        sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
        filtered_headers = {k: v for k, v in request.headers.items() if k.lower() not in sensitive_headers}
        
        sentry_sdk.set_context("request", {
            "method": request.method,
            "url": str(request.url),
            "headers": filtered_headers,
            "query_params": dict(request.query_params)
        })
    except Exception:
        # Sentry not initialized or other error, silently ignore
        pass


def capture_message_with_context(message: str, level: str, **context: Any) -> None:
    """
    Captures a message with custom context in Sentry.

    Args:
        message (str): The message to capture.
        level (str): The log level (e.g., 'info', 'warning', 'error').
        **context: Additional context key-value pairs.
    """
    try:
        sentry_sdk.capture_message(message, level=level, extra=context)
    except Exception:
        # Sentry not initialized or other error, silently ignore
        pass


def start_transaction(name: str, op: str) -> Optional[Any]:
    """
    Starts a Sentry transaction and returns it for manual instrumentation.

    Args:
        name (str): The name of the transaction.
        op (str): The operation type.

    Returns:
        Optional[Any]: The Sentry transaction object, or None if Sentry is not initialized.
    """
    try:
        return sentry_sdk.start_transaction(name=name, op=op)
    except Exception:
        # Sentry not initialized or other error, return None
        return None


def monitor_performance(operation: str) -> Callable:
    """
    Decorator that wraps functions with Sentry spans for performance monitoring.

    Args:
        operation (str): The operation type for the span.

    Returns:
        Callable: The decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                with sentry_sdk.start_span(op=operation, description=func.__name__):
                    return func(*args, **kwargs)
            except Exception:
                # If Sentry span fails, still execute the function
                return func(*args, **kwargs)
        return wrapper
    return decorator


def configure_scope_for_request(request: Request, user: Optional[Dict[str, Any]] = None) -> None:
    """
    Sets up Sentry scope with request and user context.

    Args:
        request (Request): The FastAPI request object.
        user (Optional[Dict[str, Any]]): Optional user data dictionary.
    """
    try:
        with sentry_sdk.configure_scope() as scope:
            # Set request context
            sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
            filtered_headers = {k: v for k, v in request.headers.items() if k.lower() not in sensitive_headers}
            
            scope.set_context("request", {
                "method": request.method,
                "url": str(request.url),
                "headers": filtered_headers,
                "query_params": dict(request.query_params)
            })
            
            # Set user context if provided
            if user:
                set_user_context(user)
    except Exception:
        # Sentry not initialized or other error, silently ignore
        pass