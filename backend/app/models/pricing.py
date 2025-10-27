from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from decimal import Decimal


class PricingPackageBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    features: List[dict] = Field(default_factory=list)
    max_projects: Optional[int] = None
    max_team_members: Optional[int] = None
    priority: int = 0
    is_active: bool = True


class PricingPackageCreate(PricingPackageBase):
    pass


class PricingPackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    features: Optional[List[dict]] = None
    max_projects: Optional[int] = None
    max_team_members: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class PricingPackage(PricingPackageBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PricingCampaignBase(BaseModel):
    name: str
    code: Optional[str] = None
    discount_type: str  # "percentage" or "fixed"
    discount_value: Decimal
    max_uses: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    applicable_packages: Optional[List[str]] = None
    is_active: bool = True


class PricingCampaignCreate(PricingCampaignBase):
    pass


class PricingCampaignUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    max_uses: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    applicable_packages: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PricingCampaign(PricingCampaignBase):
    id: str
    used_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserSubscriptionBase(BaseModel):
    user_id: str
    package_id: str
    campaign_id: Optional[str] = None
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    original_price: Optional[Decimal] = None
    discount_amount: Decimal = Decimal('0')
    final_price: Optional[Decimal] = None


class UserSubscriptionCreate(UserSubscriptionBase):
    pass


class UserSubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    original_price: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    final_price: Optional[Decimal] = None


class UserSubscription(UserSubscriptionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscountCalculation(BaseModel):
    original_price: Decimal
    discount_amount: Decimal
    final_price: Decimal
    discount_percentage: Optional[float] = None
    campaign_name: Optional[str] = None


class PricingResponse(BaseModel):
    packages: List[PricingPackage]
    campaigns: List[PricingCampaign] = Field(default_factory=list)