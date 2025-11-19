from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
from ..utils.logger import correlation_id_ctx

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Set in context var for logger
        token = correlation_id_ctx.set(correlation_id)
        
        try:
            response = await call_next(request)
            # Return correlation ID in response header
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            # Reset context var
            correlation_id_ctx.reset(token)
