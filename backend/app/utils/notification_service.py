"""
Notification service utility module for creating and publishing notifications.

This module provides functions to create notifications, publish them via Redis for real-time delivery,
and manage notification states. It follows the pattern of other utility modules in the project,
with graceful error handling and integration with Supabase and Redis.
"""

from ..utils.supabase_client import get_supabase_client
from ..utils.redis_client import publish_analytics_event
from ..utils.logger import logger
from datetime import datetime
from typing import Optional, Dict, Any, List


async def create_notification(
    recipient_id: str,
    notification_type: str,
    severity: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    expires_at: Optional[datetime] = None
) -> Optional[str]:
    """Create a notification and publish it for real-time delivery.

    Inserts the notification into the notifications table and publishes an event
    to the user's Redis channel for WebSocket delivery.

    Returns the notification ID if successful, None otherwise.
    """
    sb = get_supabase_client()
    data = {
        "recipient_id": recipient_id,
        "notification_type": notification_type,
        "severity": severity,
        "title": title,
        "message": message,
        "action_url": action_url,
        "metadata": metadata or {},
        "expires_at": expires_at.isoformat() if expires_at else None
    }
    
    try:
        result = sb.table("notifications").insert(data).execute()
        notification_id = result.data[0]["id"]
        
        # Publish notification event for real-time delivery
        publish_analytics_event(
            f"notifications:user:{recipient_id}",
            "notification_created",
            {"notification_id": notification_id, **data}
        )
        
        return notification_id
    except Exception as e:
        logger.warning(f"Failed to create notification: {e}")
        return None


async def create_notification_for_admins(
    notification_type: str,
    severity: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    expires_at: Optional[datetime] = None
) -> None:
    """Create notifications for all admin users.

    Queries the user_profiles table for admin users and creates notifications for each.
    """
    sb = get_supabase_client()
    
    try:
        admins = sb.table("user_profiles").select("user_id").eq("role", "admin").execute()
        admin_ids = [admin["user_id"] for admin in admins.data]
        
        for admin_id in admin_ids:
            await create_notification(
                admin_id,
                notification_type,
                severity,
                title,
                message,
                action_url,
                metadata,
                expires_at
            )
    except Exception as e:
        logger.warning(f"Failed to create notifications for admins: {e}")


async def mark_notifications_read(notification_ids: List[str], user_id: str) -> int:
    """Mark specified notifications as read for the given user.

    Updates the read_at timestamp for notifications owned by the user.
    Returns the number of notifications marked as read.
    """
    sb = get_supabase_client()
    
    try:
        result = sb.table("notifications").update({"read_at": "now()"}).in_("id", notification_ids).eq("recipient_id", user_id).execute()
        return len(result.data)
    except Exception as e:
        logger.warning(f"Failed to mark notifications read: {e}")
        return 0


async def get_unread_count(user_id: str) -> int:
    """Get the count of unread notifications for the given user.

    Returns the number of notifications with read_at = null.
    """
    sb = get_supabase_client()
    
    try:
        result = sb.table("notifications").select("id", count="exact").eq("recipient_id", user_id).is_("read_at", None).execute()
        return result.count
    except Exception as e:
        logger.warning(f"Failed to get unread count: {e}")
        return 0