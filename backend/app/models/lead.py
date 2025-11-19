from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, conint, validator
import re


class LeadData(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    message: str
    services_interested: List[str] = Field(default_factory=list)
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    source: str = Field(..., description="contact_form|strategy_session|partnership")

    @validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z0-9\s\-\.]+$", v):
            raise ValueError("Name contains invalid characters")
        return v

    @validator("phone")
    def validate_phone(cls, v):
        if v and not re.match(r"^\+?[\d\s\-\(\)]+$", v):
            raise ValueError("Invalid phone number format")
        return v

    @validator("message")
    def sanitize_message(cls, v):
        # Basic sanitization: remove potential script tags
        clean = re.sub(r"<[^>]*>", "", v)
        return clean


class LeadRequest(BaseModel):
    lead_data: LeadData
    analyze: bool = True
    auto_respond: bool = False


class LeadScore(BaseModel):
    score: conint(ge=0, le=100)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    factors: Dict[str, float] = Field(default_factory=dict)
    priority: str = Field("low")


class LeadAnalysis(BaseModel):
    lead_score: LeadScore
    recommended_services: List[str] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    estimated_value: Optional[float] = None


class LeadResponse(BaseModel):
    lead_id: str
    analysis: Optional[LeadAnalysis] = None
    status: str = Field("received")
    created_at: datetime = Field(default_factory=datetime.utcnow)
