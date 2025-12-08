from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from decimal import Decimal

from ..models.analytics import (
    TimeRangeParams,
    PaginationParams,
    LeadMetrics,
    ConversationMetrics,
    ServiceRecommendation,
    AgentPerformance,
    TimeSeriesDataPoint,
    TimeSeriesResponse,
    AnalyticsFilterParams,
    RevenueSummary,
    RevenueByPackage,
    CustomerLTV,
    SubscriptionTrendPoint,
    SubscriptionTrendsResponse,
    ModelMetrics,
)
from ..utils.auth import get_current_user, require_admin
from ..utils.supabase_client import get_supabase_client
from ..utils.logger import logger
from ..utils.cache import cache
import sentry_sdk
from collections import defaultdict

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/models/metrics", response_model=List[ModelMetrics], summary="Get AI model performance metrics", description="Retrieve aggregated performance metrics for AI models including request counts, latency, success rates, and token usage.")
async def get_model_metrics(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(require_admin),
):
    """Get performance metrics for AI models."""
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.query", description="get_model_metrics") as span:
            span.set_tag("analytics.metric", "model_metrics")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            
            # Fetch raw metrics from Supabase
            # Note: In a production env with many records, this should be an RPC call
            start_ts = time_range.start_date.timestamp()
            end_ts = time_range.end_date.timestamp()
            
            result = sb.table("model_metrics") \
                .select("*") \
                .gte("timestamp", start_ts) \
                .lte("timestamp", end_ts) \
                .execute()
                
        if not result.data:
            return []
            
        # Aggregate in memory
        metrics = defaultdict(lambda: {
            "total_requests": 0,
            "total_latency": 0.0,
            "success_count": 0,
            "total_tokens": 0,
            "error_count": 0
        })
        
        for row in result.data:
            m = metrics[row["model_name"]]
            m["total_requests"] += 1
            m["total_latency"] += row["latency"]
            m["total_tokens"] += row.get("token_usage", 0)
            if row["success"]:
                m["success_count"] += 1
            else:
                m["error_count"] += 1
                
        return [
            ModelMetrics(
                model_name=name,
                total_requests=data["total_requests"],
                avg_latency=data["total_latency"] / data["total_requests"] if data["total_requests"] > 0 else 0,
                success_rate=data["success_count"] / data["total_requests"] if data["total_requests"] > 0 else 0,
                total_tokens=data["total_tokens"],
                error_count=data["error_count"]
            )
            for name, data in metrics.items()
        ]
            
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Analytics error in get_model_metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/leads/summary", response_model=LeadMetrics, summary="Get lead conversion summary", description="Retrieve aggregated lead metrics including total leads, qualified leads, conversion rates, and average lead scores.")
@cache(ttl=300, prefix="lead_summary")
async def get_lead_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_lead_conversion_metrics") as span:
            span.set_tag("analytics.metric", "lead_summary")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc(
                "get_lead_conversion_metrics",
                {
                    "start_date": time_range.start_date,
                    "end_date": time_range.end_date,
                    "user_uuid": user_uuid,
                },
            ).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        if result.data:
            data = result.data[0]
            sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
            return LeadMetrics(
                total_leads=data["total_leads"],
                qualified_leads=data["qualified_leads"],
                conversion_rate=data["conversion_rate"],
                avg_lead_score=data["avg_lead_score"],
            )
        else:
            raise HTTPException(status_code=500, detail="No data returned from analytics function")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/summary", response_model=RevenueSummary, summary="Get revenue summary metrics", description="Retrieve key revenue metrics including MRR, ARR, total revenue, active subscriptions, and churn rate.")
@cache(ttl=300, prefix="revenue_summary")
async def get_revenue_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_revenue_summary") as span:
            span.set_tag("analytics.metric", "revenue_summary")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc('get_revenue_summary', {'start_date': time_range.start_date, 'end_date': time_range.end_date, 'user_uuid': user_uuid}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        if result.data and len(result.data) > 0:
            data = result.data[0]
            sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
            return RevenueSummary(
                mrr=data["mrr"],
                arr=data["arr"],
                total_revenue=data["total_revenue"],
                active_subscriptions=data["active_subscriptions"],
                cancelled_subscriptions=data["cancelled_subscriptions"],
                churn_rate=data["churn_rate"]
            )
        else:
            logger.error("Revenue summary RPC returned no data", extra={"user_uuid": user_uuid, "time_range": time_range.dict()})
            raise HTTPException(status_code=500, detail="No revenue summary data available for the specified time range")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Revenue analytics error in get_revenue_summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/by-package", response_model=List[RevenueByPackage], summary="Get revenue by package", description="Retrieve revenue breakdown by subscription packages including subscription counts and average revenue per package.")
async def get_revenue_by_package(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_revenue_by_package") as span:
            span.set_tag("analytics.metric", "revenue_by_package")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc('get_revenue_by_package', {'start_date': time_range.start_date, 'end_date': time_range.end_date, 'user_uuid': user_uuid}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        if not result.data:
            sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
            return []
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return [
            RevenueByPackage(
                package_id=row["package_id"],
                package_name=row["package_name"],
                subscription_count=row["subscription_count"],
                total_revenue=row["total_revenue"],
                avg_revenue_per_subscription=row["avg_revenue_per_subscription"]
            )
            for row in result.data
        ]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Revenue analytics error in get_revenue_by_package: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/subscription-trends", response_model=SubscriptionTrendsResponse, summary="Get subscription trends", description="Retrieve time-series data for subscription changes including new subscriptions, cancellations, and net growth over time.")
async def get_subscription_trends(
    time_range: TimeRangeParams = Depends(),
    aggregation: str = Query('daily', regex='^(daily|weekly)$'),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_subscription_trends") as span:
            span.set_tag("analytics.metric", "subscription_trends")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc('get_subscription_trends', {'start_date': time_range.start_date, 'end_date': time_range.end_date, 'aggregation': aggregation, 'user_uuid': user_uuid}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        data_points = [
            SubscriptionTrendPoint(
                period=row["period"],
                new_subscriptions=row["new_subscriptions"],
                cancelled_subscriptions=row["cancelled_subscriptions"],
                net_change=row["net_change"],
                cumulative_active=row["cumulative_active"]
            )
            for row in result.data
        ]
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return SubscriptionTrendsResponse(
            data=data_points,
            aggregation=aggregation
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Revenue analytics error in get_subscription_trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/customer-ltv", response_model=List[CustomerLTV], summary="Get customer lifetime value", description="Retrieve customer lifetime value metrics including total spent, subscription count, and estimated LTV for each customer.")
async def get_customer_ltv(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_customer_ltv") as span:
            span.set_tag("analytics.metric", "customer_ltv")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc('get_customer_ltv', {'user_uuid': user_uuid}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        if not result.data:
            sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
            return []
        if pagination.offset >= len(result.data):
            raise HTTPException(status_code=400, detail="Pagination offset exceeds available data")
        paginated_data = result.data[pagination.offset:pagination.offset + pagination.limit]
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return [
            CustomerLTV(
                user_id=row["user_id"],
                total_spent=row["total_spent"],
                subscription_count=row["subscription_count"],
                avg_subscription_value=row["avg_subscription_value"],
                lifetime_months=row["lifetime_months"],
                estimated_ltv=row["estimated_ltv"]
            )
            for row in paginated_data
        ]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Revenue analytics error in get_customer_ltv: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/subscriptions/list", summary="List user subscriptions", description="Retrieve a paginated list of user subscriptions with optional filtering by status and package.")
async def get_subscriptions_list(
    pagination: PaginationParams = Depends(),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.query", description="user_subscriptions select") as span:
            span.set_tag("analytics.metric", "subscriptions_list")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            query = sb.table("user_subscriptions").select("*, pricing_packages(name)")
            if current_user["role"] == "user":
                query = query.eq("user_id", current_user["user_id"])
            if filters.subscription_status:
                query = query.eq("status", filters.subscription_status)
            if filters.package_id:
                query = query.eq("package_id", filters.package_id)
            sort_by = filters.sort_by or "created_at"
            sort_order = filters.sort_order or "desc"
            query = query.order(sort_by, desc=(sort_order == "desc")).limit(pagination.limit).offset(pagination.offset)
            result = query.execute()
            total_query = sb.table("user_subscriptions").select("id", count="exact")
            if current_user["role"] == "user":
                total_query = total_query.eq("user_id", current_user["user_id"])
            if filters.subscription_status:
                total_query = total_query.eq("status", filters.subscription_status)
            if filters.package_id:
                total_query = total_query.eq("package_id", filters.package_id)
            total_result = total_query.execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return {"items": result.data, "total": total}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/leads/trends", response_model=TimeSeriesResponse, summary="Get lead creation trends", description="Retrieve time-series data for lead creation trends over the specified time range.")
async def get_lead_trends(
    time_range: TimeRangeParams = Depends(),
    aggregation: str = Query("daily", regex="^(daily|weekly)$"),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_lead_trends") as span:
            span.set_tag("analytics.metric", "lead_trends")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc("get_lead_trends", {"start_date": time_range.start_date, "end_date": time_range.end_date, "aggregation": aggregation, "user_uuid": user_uuid}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        data_points = [
            TimeSeriesDataPoint(date=row["date"].date(), value=float(row["value"]), label=None)
            for row in result.data
        ]
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return TimeSeriesResponse(
            data=data_points,
            metric_name="lead_creation_trends",
            aggregation=aggregation,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/summary", response_model=ConversationMetrics, summary="Get conversation metrics summary", description="Retrieve aggregated conversation metrics including total conversations, average messages per conversation, and active vs completed conversations.")
@cache(ttl=300, prefix="conversation_summary")
async def get_conversation_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_conversation_analytics") as span:
            span.set_tag("analytics.metric", "conversation_summary")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc(
                "get_conversation_analytics",
                {
                    "start_date": time_range.start_date,
                    "end_date": time_range.end_date,
                    "user_uuid": user_uuid,
                },
            ).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        if result.data:
            data = result.data[0]
            sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
            return ConversationMetrics(
                total_conversations=data["total_conversations"],
                avg_messages_per_conversation=data["avg_messages_per_conversation"],
                active_conversations=data["active_conversations"],
                completed_conversations=data["completed_conversations"],
            )
        else:
            raise HTTPException(status_code=500, detail="No data returned from analytics function")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/trends", response_model=TimeSeriesResponse, summary="Get conversation trends", description="Retrieve time-series data for conversation activity trends with optional filtering by status and channel.")
async def get_conversation_trends(
    time_range: TimeRangeParams = Depends(),
    aggregation: str = Query("daily", regex="^(daily|weekly)$"),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        with sentry_sdk.start_span(op="db.rpc", description="get_conversation_trends") as span:
            span.set_tag("analytics.metric", "conversation_trends")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc("get_conversation_trends", {"start_date": time_range.start_date, "end_date": time_range.end_date, "aggregation": aggregation, "user_uuid": user_uuid, "status_filter": filters.status, "channel_filter": filters.channel}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        data_points = [
            TimeSeriesDataPoint(date=row["date"].date(), value=float(row["value"]), label=None)
            for row in result.data
        ]
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return TimeSeriesResponse(
            data=data_points,
            metric_name="conversation_trends",
            aggregation=aggregation,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/list", summary="List conversations", description="Retrieve a paginated list of conversations with optional filtering by status, channel, and user.")
async def get_conversation_list(
    pagination: PaginationParams = Depends(),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.query", description="conversations select") as span:
            span.set_tag("analytics.metric", "conversation_list")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            user_filter = {"user_id": {"eq": current_user["user_id"]}} if current_user["role"] == "user" else {}
            status_filter = {"status": {"eq": filters.status}} if filters.status else {}
            channel_filter = {"channel": {"eq": filters.channel}} if filters.channel else {}
            sort_by = filters.sort_by or "created_at"
            sort_order = filters.sort_order or "desc"
            query = sb.table("conversations").select("*").match({**user_filter, **status_filter, **channel_filter}).order(sort_by, desc=(sort_order == "desc")).limit(pagination.limit).offset(pagination.offset)
            result = query.execute()
            total_query = sb.table("conversations").select("id", count="exact").match({**user_filter, **status_filter, **channel_filter})
            total_result = total_query.execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return {"items": result.data, "total": total}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/summary", response_model=List[AgentPerformance], summary="Get agent performance summary", description="Retrieve performance metrics for AI agents including action counts, success rates, and execution times.")
@cache(ttl=300, prefix="agent_summary")
async def get_agent_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(require_admin),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.rpc", description="get_agent_performance_metrics") as span:
            span.set_tag("analytics.metric", "agent_summary")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc(
                "get_agent_performance_metrics",
                {
                    "start_date": time_range.start_date,
                    "end_date": time_range.end_date,
                },
            ).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return [
            AgentPerformance(
                agent_type=row["agent_type"],
                total_actions=row["total_actions"],
                success_rate=row["success_rate"],
                avg_execution_time=row["avg_execution_time"],
                error_rate=row["error_rate"],
            )
            for row in result.data
        ]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/trends", response_model=TimeSeriesResponse, summary="Get agent performance trends", description="Retrieve time-series data for agent success rate trends with optional filtering by agent type.")
async def get_agent_trends(
    time_range: TimeRangeParams = Depends(),
    agent_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.rpc", description="get_agent_trends") as span:
            span.set_tag("analytics.metric", "agent_trends")
            span.set_tag("analytics.time_range", f"{time_range.start_date}_to_{time_range.end_date}")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            result = sb.rpc("get_agent_trends", {"start_date": time_range.start_date, "end_date": time_range.end_date, "agent_type_filter": agent_type}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        data_points = [
            TimeSeriesDataPoint(date=row["date"].date(), value=float(row["value"]), label=None)
            for row in result.data
        ]
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return TimeSeriesResponse(
            data=data_points,
            metric_name="agent_success_rate_trends",
            aggregation="daily",
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/logs", summary="Get agent logs", description="Retrieve a paginated list of agent execution logs with optional filtering by agent type and status.")
async def get_agent_logs(
    pagination: PaginationParams = Depends(),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(require_admin),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.query", description="agent_logs select") as span:
            span.set_tag("analytics.metric", "agent_logs")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            agent_type_filter = {"agent_type": {"eq": filters.agent_type}} if filters.agent_type else {}
            status_filter = {"status": {"eq": filters.status}} if filters.status else {}
            sort_by = filters.sort_by or "created_at"
            sort_order = filters.sort_order or "desc"
            query = sb.table("agent_logs").select("*").match({**agent_type_filter, **status_filter}).order(sort_by, desc=(sort_order == "desc")).limit(pagination.limit).offset(pagination.offset)
            result = query.execute()
            total_query = sb.table("agent_logs").select("id", count="exact").match({**agent_type_filter, **status_filter})
            total_result = total_query.execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return {"items": result.data, "total": total}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/services/recommendations", response_model=List[ServiceRecommendation], summary="Get service recommendations insights", description="Retrieve insights on AI-generated service recommendations including acceptance rates and confidence scores.")
async def get_service_recommendations(
    current_user: dict = Depends(get_current_user),
):
    sentry_sdk.set_user({"id": current_user["user_id"], "role": current_user["role"]})
    sb = get_supabase_client()
    try:
        with sentry_sdk.start_span(op="db.rpc", description="get_service_recommendations_insights" if current_user["role"] == "admin" else "get_service_recommendations_insights_for_user") as span:
            span.set_tag("analytics.metric", "service_recommendations")
            span.set_tag("analytics.user_role", current_user["role"])
            sentry_sdk.add_breadcrumb(message="Query started", category="db", level="info")
            if current_user["role"] == "admin":
                result = sb.rpc("get_service_recommendations_insights").execute()
            else:
                result = sb.rpc("get_service_recommendations_insights_for_user", {"user_uuid": current_user["user_id"]}).execute()
        sentry_sdk.add_breadcrumb(message="Data processing", category="analytics", level="info")
        sentry_sdk.add_breadcrumb(message="Response formatting", category="analytics", level="info")
        return [
            ServiceRecommendation(
                service_name=row["service_name"],
                total_recommendations=row["total_recommendations"],
                accepted_count=row["accepted_count"],
                acceptance_rate=row["acceptance_rate"],
                avg_confidence=row["avg_confidence"],
            )
            for row in result.data
        ]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
