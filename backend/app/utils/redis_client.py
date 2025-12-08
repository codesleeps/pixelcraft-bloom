"""
Redis client utility module for real-time analytics.

This module provides a Redis client for pub/sub operations to enable real-time updates
in the analytics dashboard. It follows the same pattern as other client utilities in the
project, with lazy initialization and graceful degradation when Redis is unavailable.

Channel naming conventions:
- analytics:leads: Events related to lead creation, updates, and analysis
- analytics:conversations: Events related to conversation messages and deletions
- analytics:revenue: Events related to subscription and revenue changes
- analytics:agents: Events related to agent logs and performance metrics

All events are published as JSON messages with the format:
{"event_type": str, "data": dict, "timestamp": str}
"""

import json
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional
import redis
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from ..utils.logger import logger


_redis_client: Optional[Any] = None


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def _create_redis_client() -> Any:
    """Create a Redis client with retry logic for connection failures."""
    return redis.from_url(settings.redis_url)


@lru_cache()
def get_redis_client() -> Optional[Any]:
    """Create and return a Redis client instance using the configured Redis URL.

    This function lazily initializes the Redis client on first call. If redis_url
    is not configured in settings, returns None for graceful degradation.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if not settings.redis_url:
        logger.warning("Redis URL not configured in settings; Redis functionality disabled")
        return None

    try:
        _redis_client = _create_redis_client()
        logger.info("Redis client initialized with URL: %s", settings.redis_url)
        return _redis_client
    except Exception as exc:
        logger.exception("Failed to initialize Redis client after retries: %s", exc)
        return None


def test_redis_connection() -> bool:
    """Test Redis connectivity by attempting to ping the server.

    Returns True if the ping succeeds, False otherwise. If Redis is not configured,
    returns False.
    """
    client = get_redis_client()
    if client is None:
        return False

    try:
        client.ping()
        return True
    except Exception as exc:
        logger.exception("Redis connectivity test failed: %s", exc)
        return False


def publish_analytics_event(channel: str, event_type: str, data: Dict[str, Any]) -> None:
    """Publish an analytics event to a Redis pub/sub channel.

    The event is serialized as JSON with the format:
    {"event_type": event_type, "data": data, "timestamp": datetime.now().isoformat()}

    If Redis is unavailable, logs a warning and continues without publishing.
    """
    client = get_redis_client()
    if client is None:
        logger.warning("Redis client not available; skipping event publication for channel: %s", channel)
        return

    message = {
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

    try:
        client.publish(channel, json.dumps(message))
        logger.debug("Published analytics event to channel %s: %s", channel, event_type)
    except Exception as exc:
        logger.exception("Failed to publish analytics event to channel %s: %s", channel, exc)


def subscribe_to_analytics_events(channels: List[str]) -> Optional[Any]:
    """Subscribe to the specified Redis pub/sub channels for analytics events.

    Returns a Redis pubsub object if successful, or None if Redis is unavailable.
    The caller is responsible for managing the pubsub lifecycle.
    """
    client = get_redis_client()
    if client is None:
        logger.warning("Redis client not available; cannot subscribe to channels: %s", channels)
        return None

    try:
        pubsub = client.pubsub()
        pubsub.subscribe(*channels)
        logger.info("Subscribed to analytics channels: %s", channels)
        return pubsub
    except Exception as exc:
        logger.exception("Failed to subscribe to analytics channels %s: %s", channels, exc)
        return None