import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..config import settings
from ..utils.supabase_client import get_supabase_client


router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger("pixelcraft.payments")


def init_stripe() -> None:
    if not settings.stripe or not settings.stripe.api_key:
        raise RuntimeError("Stripe not configured. Set STRIPE_API_KEY and related variables.")
    stripe.api_key = settings.stripe.api_key


class CheckoutRequest(BaseModel):
    price_id: Optional[str] = None
    mode: Optional[str] = "subscription"  # or "payment"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/create-checkout-session")
async def create_checkout_session(body: CheckoutRequest):
    try:
        init_stripe()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    price_id = body.price_id or (settings.stripe.default_price_id if settings.stripe else None)
    if not price_id:
        raise HTTPException(status_code=400, detail="price_id is required (or configure STRIPE_PRICE_ID)")

    mode = body.mode or (settings.stripe.mode if settings.stripe else "subscription")
    success_url = body.success_url or (settings.stripe.success_url if settings.stripe else None)
    cancel_url = body.cancel_url or (settings.stripe.cancel_url if settings.stripe else None)

    if not success_url or not cancel_url:
        raise HTTPException(status_code=400, detail="success_url and cancel_url are required (or configure STRIPE_SUCCESS_URL/STRIPE_CANCEL_URL)")

    try:
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
            customer_email=body.customer_email,
            metadata=body.metadata or {},
        )
        return {"id": session.id, "url": session.url}
    except Exception as exc:
        logger.exception("Failed to create Stripe checkout session: %s", exc)
        raise HTTPException(status_code=500, detail="Stripe error creating checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.stripe or not settings.stripe.webhook_secret:
        logger.error("Stripe webhook secret not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")

    try:
        init_stripe()
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe.webhook_secret)
    except Exception as exc:
        logger.warning("Invalid Stripe webhook signature: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    client = get_supabase_client()

    # Handle key events minimally; persist subscription summary to Supabase
    try:
        if event_type == "checkout.session.completed":
            email = (obj.get("customer_details") or {}).get("email")
            amount_total = obj.get("amount_total")
            metadata = obj.get("metadata") or {}

            user_id = None
            if email and hasattr(client, "table"):
                try:
                    res = client.table("auth.users").select("id,email").eq("email", email).limit(1).execute()
                    rows = getattr(res, "data", [])
                    if rows:
                        user_id = rows[0].get("id")
                except Exception as e:
                    logger.warning("Lookup in auth.users failed: %s", e)

            record = {
                "user_id": user_id,
                "package_id": metadata.get("package_id"),
                "status": "active",
                "start_date": datetime.now(timezone.utc).isoformat(),
                "final_price": (amount_total / 100.0) if amount_total else None,
            }
            record = {k: v for k, v in record.items() if v is not None}

            if hasattr(client, "table"):
                client.table("user_subscriptions").insert(record).execute()
            logger.info("Recorded subscription for email=%s user_id=%s", email, user_id)

        elif event_type in ("customer.subscription.deleted", "customer.subscription.cancelled", "customer.subscription.canceled"):
            # If needed, update user_subscriptions to cancelled. Mapping requires user/context; implement later.
            logger.info("Received subscription cancel event: %s", obj.get("id"))

    except Exception as exc:
        logger.exception("Error handling Stripe webhook: %s", exc)

    return {"received": True}

