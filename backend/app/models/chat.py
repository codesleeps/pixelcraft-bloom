from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ChatMessage(BaseModel):
    role: str = Field(..., description="user|assistant|system")
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = True

    @validator("message")
    def message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("message must not be empty")
        if len(v) > 10000:
            raise ValueError("message too long")
        return v


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent_type: str = "chat"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatStreamChunk(BaseModel):
    chunk: str
    done: bool = False
    metadata: Optional[Dict[str, Any]] = None
