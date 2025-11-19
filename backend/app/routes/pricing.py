from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from supabase import Client

from ..models.pricing import (
    PricingPackage,
    PricingPackageCreate,
    PricingPackageUpdate,
    PricingCampaign,
    PricingCampaignCreate,
    PricingCampaignUpdate,
    UserSubscription,
    UserSubscriptionCreate,
    UserSubscriptionUpdate,
    DiscountCalculation,
    PricingResponse
)
from ..utils.supabase_client import get_supabase_client
from ..utils.redis_client import publish_analytics_event
from ..utils.cache import cache

router = APIRouter()
supabase: Client = get_supabase_client()


@router.get("/packages", response_model=List[PricingPackage])
@cache(ttl=3600, prefix="pricing_packages")
async def get_pricing_packages():
    """Get all active pricing packages."""
    try:
        result = supabase.table("pricing_packages").select("*").eq("is_active", True).order("priority").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaigns/{code}", response_model=PricingCampaign)
async def get_campaign_by_code(code: str):
    """Get a pricing campaign by discount code."""
    try:
        result = supabase.table("pricing_campaigns").select("*").eq("code", code).eq("is_active", True).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign is within date range
        campaign = result.data
        now = datetime.utcnow()

        if campaign["start_date"] and now < campaign["start_date"]:
            raise HTTPException(status_code=400, detail="Campaign not yet started")

        if campaign["end_date"] and now > campaign["end_date"]:
            raise HTTPException(status_code=400, detail="Campaign has expired")

        return campaign
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-discount", response_model=DiscountCalculation)
async def calculate_discount(
    package_id: str,
    campaign_code: Optional[str] = None,
    billing_cycle: str = "monthly"  # "monthly" or "yearly"
):
    """Calculate discount for a package with optional campaign code."""
    try:
        # Get package
        package_result = supabase.table("pricing_packages").select("*").eq("id", package_id).single().execute()
        if not package_result.data:
            raise HTTPException(status_code=404, detail="Package not found")

        package = package_result.data
        original_price = Decimal(str(package[f"price_{billing_cycle}"] or 0))

        discount_amount = Decimal('0')
        campaign_name = None

        if campaign_code:
            # Get and validate campaign
            campaign_result = supabase.table("pricing_campaigns").select("*").eq("code", campaign_code).eq("is_active", True).single().execute()

            if not campaign_result.data:
                raise HTTPException(status_code=404, detail="Campaign not found")

            campaign = campaign_result.data
            now = datetime.utcnow()

            # Check date range
            if campaign["start_date"] and now < campaign["start_date"]:
                raise HTTPException(status_code=400, detail="Campaign not yet started")
            if campaign["end_date"] and now > campaign["end_date"]:
                raise HTTPException(status_code=400, detail="Campaign has expired")

            # Check usage limit
            if campaign["max_uses"] and campaign["used_count"] >= campaign["max_uses"]:
                raise HTTPException(status_code=400, detail="Campaign usage limit reached")

            # Check if package is applicable
            if campaign["applicable_packages"] and package_id not in campaign["applicable_packages"]:
                raise HTTPException(status_code=400, detail="Campaign not applicable to this package")

            # Calculate discount
            if campaign["discount_type"] == "percentage":
                discount_amount = (original_price * Decimal(str(campaign["discount_value"]))) / 100
            elif campaign["discount_type"] == "fixed":
                discount_amount = Decimal(str(campaign["discount_value"]))

            campaign_name = campaign["name"]

        final_price = original_price - discount_amount
        discount_percentage = (discount_amount / original_price * 100) if original_price > 0 else 0

        return DiscountCalculation(
            original_price=original_price,
            discount_amount=discount_amount,
            final_price=final_price,
            discount_percentage=float(discount_percentage) if campaign_code else None,
            campaign_name=campaign_name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscriptions", response_model=UserSubscription)
async def create_subscription(subscription: UserSubscriptionCreate):
    """Create a new user subscription."""
    try:
        # Calculate pricing details
        billing_cycle = "monthly"  # Default, could be determined from package
        discount_calc = await calculate_discount(subscription.package_id, subscription.campaign_id, billing_cycle)

        # Set subscription dates
        start_date = datetime.utcnow()
        if billing_cycle == "yearly":
            end_date = start_date + timedelta(days=365)
        else:
            end_date = start_date + timedelta(days=30)

        # Update campaign usage if applicable
        if subscription.campaign_id:
            await supabase.table("pricing_campaigns").update({"used_count": supabase.table("pricing_campaigns").select("used_count").eq("id", subscription.campaign_id).single().execute().data["used_count"] + 1}).eq("id", subscription.campaign_id).execute()

        # Create subscription
        subscription_data = subscription.dict()
        subscription_data.update({
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "original_price": float(discount_calc.original_price),
            "discount_amount": float(discount_calc.discount_amount),
            "final_price": float(discount_calc.final_price),
            "status": "active"
        })

        result = supabase.table("user_subscriptions").insert(subscription_data).execute()
        subscription_id = result.data[0]["id"]
        try:
            publish_analytics_event("analytics:revenue", "subscription_created", {
                "subscription_id": subscription_id,
                "user_id": subscription.user_id,
                "package_id": subscription.package_id
            })
        except Exception as e:
            logger.warning("Failed to publish subscription creation event: %s", e)
        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions/user/{user_id}", response_model=List[UserSubscription])
async def get_user_subscriptions(user_id: str):
    """Get all subscriptions for a user."""
    try:
        result = supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str):
    """Cancel a user subscription."""
    try:
        result = supabase.table("user_subscriptions").update({
            "status": "cancelled",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", subscription_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Subscription not found")

        try:
            publish_analytics_event("analytics:revenue", "subscription_updated", {
                "subscription_id": subscription_id,
                "status": "cancelled"
            })
        except Exception as e:
            logger.warning("Failed to publish subscription cancellation event: %s", e)

        return {"message": "Subscription cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
