from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime

from ..models.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
)
from ..utils.auth import get_current_user
from ..utils.supabase_client import get_supabase_client
from ..utils.notification_service import mark_notifications_read, get_unread_count

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(50),
    offset: int = Query(0),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        query = sb.table("notifications").select("*").eq("recipient_id", current_user["user_id"])
        if unread_only:
            query = query.is_("read_at", None)
        if notification_type:
            query = query.eq("notification_type", notification_type)
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        result = query.execute()
        notifications = [
            NotificationResponse(
                id=row["id"],
                recipient_id=row["recipient_id"],
                notification_type=row["notification_type"],
                severity=row["severity"],
                title=row["title"],
                message=row["message"],
                action_url=row["action_url"],
                metadata=row["metadata"],
                read_at=row["read_at"],
                created_at=row["created_at"],
            )
            for row in result.data
        ]
        total_query = sb.table("notifications").select("id", count="exact").eq("recipient_id", current_user["user_id"])
        if unread_only:
            total_query = total_query.is_("read_at", None)
        if notification_type:
            total_query = total_query.eq("notification_type", notification_type)
        total_result = total_query.execute()
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        unread_count = await get_unread_count(current_user["user_id"])
        return NotificationListResponse(
            notifications=notifications,
            total=total,
            unread_count=unread_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        result = sb.table("notifications").select("*").eq("id", notification_id).eq("recipient_id", current_user["user_id"]).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        row = result.data[0]
        return NotificationResponse(
            id=row["id"],
            recipient_id=row["recipient_id"],
            notification_type=row["notification_type"],
            severity=row["severity"],
            title=row["title"],
            message=row["message"],
            action_url=row["action_url"],
            metadata=row["metadata"],
            read_at=row["read_at"],
            created_at=row["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/mark-read")
async def mark_read(
    request: NotificationMarkReadRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        count = await mark_notifications_read(request.notification_ids, current_user["user_id"])
        return {"marked_read_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notifications as read: {str(e)}")


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        result = sb.table("notifications").update({"read_at": datetime.now().isoformat()}).eq("recipient_id", current_user["user_id"]).is_("read_at", None).execute()
        count = len(result.data) if result.data else 0
        return {"marked_read_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking all notifications as read: {str(e)}")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        # Soft delete by setting expires_at to now
        result = sb.table("notifications").update({"expires_at": datetime.now().isoformat()}).eq("id", notification_id).eq("recipient_id", current_user["user_id"]).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting notification: {str(e)}")


@router.get("/unread-count")
async def get_unread_count_endpoint(
    current_user: dict = Depends(get_current_user),
):
    try:
        count = await get_unread_count(current_user["user_id"])
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting unread count: {str(e)}")