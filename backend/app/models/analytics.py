from __future__ import annotations
from typing import Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class TimeRangeParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def set_defaults(cls, v, info):
        if v is None:
            if info.field_name == 'start_date':
                return datetime.utcnow() - timedelta(days=30)
            else:
                return datetime.utcnow()
        return v


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class LeadMetrics(BaseModel):
    total_leads: int
    qualified_leads: int
    conversion_rate: float
    avg_lead_score: float


class ConversationMetrics(BaseModel):
    total_conversations: int
    avg_messages_per_conversation: float
    active_conversations: int
    completed_conversations: int


class ServiceRecommendation(BaseModel):
    service_name: str
    total_recommendations: int
    accepted_count: int
    acceptance_rate: float
    avg_confidence: float


class AgentPerformance(BaseModel):
    agent_type: str
    total_actions: int
    success_rate: float
    avg_execution_time: float
    error_rate: float


class TimeSeriesDataPoint(BaseModel):
    date: date
    value: float
    label: Optional[str] = None


class TimeSeriesResponse(BaseModel):
    data: List[TimeSeriesDataPoint]
    metric_name: str
    aggregation: str


class AnalyticsFilterParams(BaseModel):
    status: Optional[str] = None
    agent_type: Optional[str] = None
    channel: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = 'desc'
    package_id: Optional[str] = None
    subscription_status: Optional[str] = None
   
   
class RevenueSummary(BaseModel):
    mrr: Decimal
    arr: Decimal
    total_revenue: Decimal
    active_subscriptions: int
    cancelled_subscriptions: int
    churn_rate: float
   
   
class RevenueByPackage(BaseModel):
    package_id: str
    package_name: str
    subscription_count: int
    total_revenue: Decimal
    avg_revenue_per_subscription: Decimal
   
   
class SubscriptionTrendPoint(BaseModel):
    period: datetime
    new_subscriptions: int
    cancelled_subscriptions: int
    net_change: int
    cumulative_active: int
   
   
class CustomerLTV(BaseModel):
    user_id: str
    total_spent: Decimal
    subscription_count: int
    avg_subscription_value: Decimal
    lifetime_months: float
    estimated_ltv: Decimal
   
   
class SubscriptionTrendsResponse(BaseModel):
    data: List[SubscriptionTrendPoint]
    aggregation: str
