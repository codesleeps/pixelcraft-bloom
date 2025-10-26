from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, conint


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
