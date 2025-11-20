import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse
from ..config import settings

# Custom key function to use User ID if available, otherwise IP
def get_rate_limit_key(request: Request) -> str:
    # Try to get user_id from state (if auth middleware set it)
    if hasattr(request.state, "user") and request.state.user:
        return str(request.state.user.get("id"))
    
    # Fallback to IP address
    return get_remote_address(request)

# Initialize Limiter
# We use the Redis URL from settings if available, otherwise memory fallback (though Redis is requested)
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=settings.redis_url if settings.redis_url else "memory://",
    strategy="fixed-window" # or "moving-window"
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for RateLimitExceeded exceptions.
    Returns a JSON response with a 429 status code and details.
    """
    response = JSONResponse(
        {"error": f"Rate limit exceeded: {exc.detail}"}, status_code=429
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response
