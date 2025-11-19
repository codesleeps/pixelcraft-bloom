import json
import hashlib
import asyncio
import functools
from typing import Optional, Any, Callable, Union
from datetime import datetime, timedelta
from fastapi import Request, Response

from .redis_client import get_redis_client
from .logger import logger

def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str = "") -> str:
    """Generate a deterministic cache key based on function arguments."""
    # Filter out args that shouldn't be part of the key (like Request or Response objects if needed)
    # For now, we assume all args are serializable or str-able
    
    key_parts = [prefix or func.__name__]
    
    for arg in args:
        if hasattr(arg, 'dict'):  # Pydantic models
            key_parts.append(str(sorted(arg.dict().items())))
        elif isinstance(arg, (Request, Response)):
            continue # Skip request/response objects
        else:
            key_parts.append(str(arg))
            
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'dict'):
            key_parts.append(f"{k}:{sorted(v.dict().items())}")
        elif isinstance(v, (Request, Response)):
            continue
        else:
            key_parts.append(f"{k}:{v}")
            
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache(ttl: int = 60, prefix: str = ""):
    """
    Redis cache decorator for async functions.
    
    Args:
        ttl: Time to live in seconds
        prefix: Optional prefix for the cache key
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            redis = get_redis_client()
            if not redis:
                return await func(*args, **kwargs)
            
            try:
                # Generate key
                cache_key = f"cache:{prefix or func.__name__}:{_generate_cache_key(func, args, kwargs)}"
                
                # Check cache
                cached_data = redis.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache hit for {cache_key}")
                    return json.loads(cached_data)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Serialize result
                # Handle Pydantic models
                if hasattr(result, 'dict'):
                    data_to_cache = result.dict()
                elif isinstance(result, list):
                    data_to_cache = [item.dict() if hasattr(item, 'dict') else item for item in result]
                else:
                    data_to_cache = result
                
                # Store in cache
                redis.setex(cache_key, ttl, json.dumps(data_to_cache, default=str))
                
                return result
            except Exception as e:
                logger.error(f"Cache error: {e}")
                # Fallback to original function execution on cache error
                return await func(*args, **kwargs)
                
        return wrapper
    return decorator
