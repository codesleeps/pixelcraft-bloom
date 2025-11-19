import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..config import settings
from ..utils.supabase_client import get_supabase_client
from ..utils.logger import logger, audit_logger


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


def _map_stripe_status(status: Optional[str]) -> str:
    mapping = {
        "active": "active",
        "trialing": "active",
        "paused": "paused",
        "canceled": "cancelled",
        "incomplete_expired": "expired",
        "past_due": "pending",
        "unpaid": "pending",
        "incomplete": "pending",
    }
    return mapping.get(status or "", "pending")


def _ts_to_dt(ts: Optional[int]) -> Optional[str]:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _find_user_id_by_email(client: Any, email: Optional[str]) -> Optional[str]:
    if not email or not hasattr(client, "table"):
        return None
    try:
        res = client.table("auth.users").select("id,email").eq("email", email).limit(1).execute()
        rows = getattr(res, "data", [])
        if rows:
            return rows[0].get("id")
    except Exception as e:
        logger.warning("Lookup in auth.users failed: %s", e)
    return None


def _upsert_subscription(client: Any, sub: Dict[str, Any], email: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Insert or update a user_subscriptions row based on Stripe subscription object.

    Returns (record_id, user_id).
    """
    if not hasattr(client, "table"):
        return (None, None)

    user_id = _find_user_id_by_email(client, email)
    sub_id = sub.get("id")
    price_id = None
    try:
        items = (sub.get("items") or {}).get("data") or []
        if items:
            price = items[0].get("price") or {}
            price_id = price.get("id") or sub.get("plan", {}).get("id")
    except Exception:
        price_id = None

    # Attempt to resolve package_id via pricing_packages.stripe_price_id
    package_id = None
    if price_id and hasattr(client, "table"):
        try:
            pkg = client.table("pricing_packages").select("id").eq("stripe_price_id", price_id).limit(1).execute()
            rows = getattr(pkg, "data", [])
            if rows:
                package_id = rows[0].get("id")
        except Exception as e:
            logger.warning("Failed mapping package by price_id=%s: %s", price_id, e)

    record = {
        "user_id": user_id,
        "stripe_customer_id": sub.get("customer"),
        "stripe_subscription_id": sub_id,
        "stripe_price_id": price_id,
        "stripe_status": sub.get("status"),
        "status": _map_stripe_status(sub.get("status")),
        "current_period_start": _ts_to_dt(sub.get("current_period_start")),
        "current_period_end": _ts_to_dt(sub.get("current_period_end")),
        "cancel_at_period_end": sub.get("cancel_at_period_end"),
        "canceled_at": _ts_to_dt(sub.get("canceled_at")),
        "billing_cycle_anchor": _ts_to_dt(sub.get("billing_cycle_anchor")),
        "pause_collection": bool(sub.get("pause_collection")) if sub.get("pause_collection") is not None else None,
        "package_id": package_id,
    }
    # Remove None values
    record = {k: v for k, v in record.items() if v is not None}

    try:
        existing = client.table("user_subscriptions").select("id").eq("stripe_subscription_id", sub_id).limit(1).execute()
        rows = getattr(existing, "data", [])
        if rows:
            rec_id = rows[0].get("id")
            client.table("user_subscriptions").update(record).eq("id", rec_id).execute()
            return (rec_id, user_id)
        else:
            # if we don't have start_date yet, set it from current_period_start
            if "current_period_start" in record and "start_date" not in record:
                record["start_date"] = record["current_period_start"]
            inserted = client.table("user_subscriptions").insert(record).execute()
            data = getattr(inserted, "data", [])
            rec_id = data[0].get("id") if data else None
            return (rec_id, user_id)
    except Exception as e:
        logger.exception("Failed to upsert subscription: %s", e)
        return (None, user_id)


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
        audit_logger.log_event("checkout_session_created", None, {"mode": mode, "price_id": price_id, "customer_email": body.customer_email}, status="success")
        return {"id": session.id, "url": session.url}
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        audit_logger.log_event("checkout_session_failed", None, {"error": str(e), "customer_email": body.customer_email}, status="failure")
        raise HTTPException(status_code=500, detail=str(e))


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
        audit_logger.log_event("webhook_signature_invalid", None, {"error": str(exc)}, status="failure")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    client = get_supabase_client()

    # Handle key events minimally; persist subscription summary to Supabase
    try:
        if event_type == "checkout.session.completed":
            email = (obj.get("customer_details") or {}).get("email")
            amount_total = obj.get("amount_total")
            currency = obj.get("currency")
            metadata = obj.get("metadata") or {}
            mode = obj.get("mode")

            # If this is a subscription checkout, we can pull the subscription details
            subscription_id = obj.get("subscription")
            if subscription_id:
                try:
                    sub = stripe.Subscription.retrieve(subscription_id, expand=["items.data.price"])
                    rec_id, user_id = _upsert_subscription(client, sub, email=email)
                    # update optional fields like package mapping and price
                    extra = {"package_id": metadata.get("package_id"), "final_price": (amount_total / 100.0) if amount_total else None, "currency": currency, "mode": mode}
                    extra = {k: v for k, v in extra.items() if v is not None}
                    if rec_id and hasattr(client, "table") and extra:
                        client.table("user_subscriptions").update(extra).eq("id", rec_id).execute()
                    logger.info("Recorded subscription via checkout: sub_id=%s email=%s", subscription_id, email)
                    audit_logger.log_event("checkout_session_completed_subscription", user_id, {"subscription_id": subscription_id, "email": email, "mode": mode, "amount_total": amount_total}, status="success")
                except Exception as e:
                    logger.exception("Failed retrieving subscription after checkout: %s", e)
                    audit_logger.log_event("checkout_session_completed_subscription_failed", None, {"subscription_id": subscription_id, "email": email, "error": str(e)}, status="failure")
            else:
                # Non-subscription checkout: still record a payment
                user_id = _find_user_id_by_email(client, email)
                record = {
                    "user_id": user_id,
                    "status": "active",
                    "start_date": datetime.now(timezone.utc).isoformat(),
                    "final_price": (amount_total / 100.0) if amount_total else None,
                    "currency": currency,
                    "mode": mode,
                }
                record = {k: v for k, v in record.items() if v is not None}
                if hasattr(client, "table"):
                    client.table("user_subscriptions").insert(record).execute()
                logger.info("Recorded one-time payment for email=%s", email)
                audit_logger.log_event("checkout_session_completed_one_time_payment", user_id, {"email": email, "mode": mode, "amount_total": amount_total}, status="success")

        elif event_type == "customer.subscription.updated":
            # Map pause/resume and general updates
            rec_id, user_id = _upsert_subscription(client, obj)
            logger.info("Updated subscription %s for user_id=%s", obj.get("id"), user_id)
            audit_logger.log_event("subscription_updated", user_id, {"subscription_id": obj.get("id"), "status": obj.get("status")}, status="success")

        elif event_type in ("customer.subscription.deleted", "customer.subscription.cancelled", "customer.subscription.canceled"):
            sub_id = obj.get("id")
            try:
                # mark as cancelled and set end dates
                update = {
                    "status": "cancelled",
                    "stripe_status": obj.get("status"),
                    "canceled_at": _ts_to_dt(obj.get("canceled_at")) or datetime.now(timezone.utc).isoformat(),
                    "end_date": _ts_to_dt(obj.get("current_period_end")),
                }
                update = {k: v for k, v in update.items() if v is not None}
                if hasattr(client, "table"):
                    client.table("user_subscriptions").update(update).eq("stripe_subscription_id", sub_id).execute()
                logger.info("Cancelled subscription %s", sub_id)
                audit_logger.log_event("subscription_canceled", None, {"subscription_id": sub_id}, status="success")
            except Exception as e:
                logger.exception("Failed to update cancellation for subscription %s: %s", sub_id, e)
        elif event_type in ("invoice.payment_succeeded", "invoice.payment_failed"):
            inv = obj
            sub_id = inv.get("subscription")
            intent_id = (inv.get("payment_intent") if isinstance(inv.get("payment_intent"), str) else (inv.get("payment_intent") or {}).get("id"))
            status = "succeeded" if event_type == "invoice.payment_succeeded" else "failed"
            amount_paid = inv.get("amount_paid") or inv.get("amount_due")
            next_attempt_ts = inv.get("next_payment_attempt")
            try:
                update = {
                    "stripe_invoice_id": inv.get("id"),
                    "latest_payment_intent_id": intent_id,
                    "last_payment_status": status,
                    "last_payment_at": _ts_to_dt(inv.get("status_transitions", {}).get("paid_at")) or _ts_to_dt(inv.get("created")),
                    "last_payment_amount": (amount_paid / 100.0) if amount_paid else None,
                    "next_payment_attempt": _ts_to_dt(next_attempt_ts),
                }
                update = {k: v for k, v in update.items() if v is not None}
                if hasattr(client, "table") and sub_id:
                    client.table("user_subscriptions").update(update).eq("stripe_subscription_id", sub_id).execute()
                logger.info("Updated invoice %s status=%s for subscription %s", inv.get("id"), status, sub_id)
                
                if status == "succeeded":
                    audit_logger.log_event("payment_succeeded", None, {"invoice_id": inv.get("id"), "amount": amount_paid, "subscription_id": sub_id}, status="success")
                else:
                    audit_logger.log_event("payment_failed", None, {"invoice_id": inv.get("id"), "subscription_id": sub_id}, status="failure")
                    
            except Exception as e:
                logger.exception("Failed to update invoice status for subscription %s: %s", sub_id, e)
                audit_logger.log_event("payment_processing_error", None, {"error": str(e), "invoice_id": inv.get("id")}, status="failure")

    except Exception as exc:
        logger.exception("Error handling Stripe webhook: %s", exc)

    return {"received": True}
