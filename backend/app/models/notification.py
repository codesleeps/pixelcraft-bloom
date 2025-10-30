from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    notification_type: str = Field(..., description="Type: lead, agent, workflow, system, conversation")
    severity: str = Field("info", description="Severity: info, success, warning, error")
    title: str
    message: str
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[str] = None


class NotificationCreate(NotificationBase):
    recipient_id: str


class NotificationResponse(NotificationBase):
    id: str
    recipient_id: str
    read_at: Optional[str] = None
    created_at: str


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationMarkReadRequest(BaseModel):
    notification_ids: List[str]