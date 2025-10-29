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
)
from ..utils.auth import get_current_user, require_admin
from ..utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/leads/summary", response_model=LeadMetrics)
async def get_lead_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        result = sb.rpc(
            "get_lead_conversion_metrics",
            {
                "start_date": time_range.start_date,
                "end_date": time_range.end_date,
                "user_uuid": user_uuid,
            },
        ).execute()
        if result.data:
            data = result.data[0]
            return LeadMetrics(
                total_leads=data["total_leads"],
                qualified_leads=data["qualified_leads"],
                conversion_rate=data["conversion_rate"],
                avg_lead_score=data["avg_lead_score"],
            )
        else:
            raise HTTPException(status_code=500, detail="No data returned from analytics function")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/summary", response_model=RevenueSummary)
async def get_revenue_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        result = sb.rpc('get_revenue_summary', {'start_date': time_range.start_date, 'end_date': time_range.end_date, 'user_uuid': user_uuid}).execute()
        if result.data:
            data = result.data[0]
            return RevenueSummary(
                mrr=data["mrr"],
                arr=data["arr"],
                total_revenue=data["total_revenue"],
                active_subscriptions=data["active_subscriptions"],
                cancelled_subscriptions=data["cancelled_subscriptions"],
                churn_rate=data["churn_rate"]
            )
        else:
            raise HTTPException(status_code=500, detail="No data returned from analytics function")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/by-package", response_model=List[RevenueByPackage])
async def get_revenue_by_package(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        result = sb.rpc('get_revenue_by_package', {'start_date': time_range.start_date, 'end_date': time_range.end_date, 'user_uuid': user_uuid}).execute()
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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/subscription-trends", response_model=SubscriptionTrendsResponse)
async def get_subscription_trends(
    time_range: TimeRangeParams = Depends(),
    aggregation: str = Query('daily', regex='^(daily|weekly)$'),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        result = sb.rpc('get_subscription_trends', {'start_date': time_range.start_date, 'end_date': time_range.end_date, 'aggregation': aggregation, 'user_uuid': user_uuid}).execute()
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
        return SubscriptionTrendsResponse(
            data=data_points,
            aggregation=aggregation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/customer-ltv", response_model=List[CustomerLTV])
async def get_customer_ltv(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        result = sb.rpc('get_customer_ltv', {'user_uuid': user_uuid}).execute()
        paginated_data = result.data[pagination.offset:pagination.offset + pagination.limit]
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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/revenue/subscriptions/list")
async def get_subscriptions_list(
    pagination: PaginationParams = Depends(),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
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
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        return {"items": result.data, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/leads/trends", response_model=TimeSeriesResponse)
async def get_lead_trends(
    time_range: TimeRangeParams = Depends(),
    aggregation: str = Query("daily", regex="^(daily|weekly)$"),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_filter = f" AND user_id = '{current_user['user_id']}'" if current_user["role"] == "user" else ""
        trunc_unit = "day" if aggregation == "daily" else "week"
        query = f"""
        SELECT 
            date_trunc('{trunc_unit}', created_at) as date,
            count(*) as value
        FROM leads
        WHERE created_at BETWEEN '{time_range.start_date}' AND '{time_range.end_date}'
        AND deleted_at IS NULL{user_filter}
        GROUP BY date
        ORDER BY date
        """
        result = sb.rpc("execute_sql", {"query": query}).execute()  # Assuming a helper RPC for raw queries, or use table select
        # Note: Supabase client may not support raw SQL directly; adjust if needed
        data_points = [
            TimeSeriesDataPoint(date=row["date"].date(), value=row["value"], label=None)
            for row in result.data
        ]
        return TimeSeriesResponse(
            data=data_points,
            metric_name="lead_creation_trends",
            aggregation=aggregation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/summary", response_model=ConversationMetrics)
async def get_conversation_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_uuid = current_user["user_id"] if current_user["role"] == "user" else None
        result = sb.rpc(
            "get_conversation_analytics",
            {
                "start_date": time_range.start_date,
                "end_date": time_range.end_date,
                "user_uuid": user_uuid,
            },
        ).execute()
        if result.data:
            data = result.data[0]
            return ConversationMetrics(
                total_conversations=data["total_conversations"],
                avg_messages_per_conversation=data["avg_messages_per_conversation"],
                active_conversations=data["active_conversations"],
                completed_conversations=data["completed_conversations"],
            )
        else:
            raise HTTPException(status_code=500, detail="No data returned from analytics function")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/trends", response_model=TimeSeriesResponse)
async def get_conversation_trends(
    time_range: TimeRangeParams = Depends(),
    aggregation: str = Query("daily", regex="^(daily|weekly)$"),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_filter = f" AND user_id = '{current_user['user_id']}'" if current_user["role"] == "user" else ""
        status_filter = f" AND status = '{filters.status}'" if filters.status else ""
        channel_filter = f" AND channel = '{filters.channel}'" if filters.channel else ""
        trunc_unit = "day" if aggregation == "daily" else "week"
        sort_order = filters.sort_order or "desc"
        query = f"""
        SELECT 
            date_trunc('{trunc_unit}', created_at) as date,
            count(*) as value
        FROM conversations
        WHERE created_at BETWEEN '{time_range.start_date}' AND '{time_range.end_date}'
        AND deleted_at IS NULL{user_filter}{status_filter}{channel_filter}
        GROUP BY date
        ORDER BY date {sort_order}
        """
        result = sb.rpc("execute_sql", {"query": query}).execute()  # Adjust for actual Supabase query method
        data_points = [
            TimeSeriesDataPoint(date=row["date"].date(), value=row["value"], label=None)
            for row in result.data
        ]
        return TimeSeriesResponse(
            data=data_points,
            metric_name="conversation_trends",
            aggregation=aggregation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/conversations/list")
async def get_conversation_list(
    pagination: PaginationParams = Depends(),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        user_filter = {"user_id": {"eq": current_user["user_id"]}} if current_user["role"] == "user" else {}
        status_filter = {"status": {"eq": filters.status}} if filters.status else {}
        channel_filter = {"channel": {"eq": filters.channel}} if filters.channel else {}
        sort_by = filters.sort_by or "created_at"
        sort_order = filters.sort_order or "desc"
        query = sb.table("conversations").select("*").match({**user_filter, **status_filter, **channel_filter}).order(sort_by, desc=(sort_order == "desc")).limit(pagination.limit).offset(pagination.offset)
        result = query.execute()
        total_query = sb.table("conversations").select("id", count="exact").match({**user_filter, **status_filter, **channel_filter})
        total_result = total_query.execute()
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        return {"items": result.data, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/summary", response_model=List[AgentPerformance])
async def get_agent_summary(
    time_range: TimeRangeParams = Depends(),
    current_user: dict = Depends(require_admin),
):
    sb = get_supabase_client()
    try:
        result = sb.rpc(
            "get_agent_performance_metrics",
            {
                "start_date": time_range.start_date,
                "end_date": time_range.end_date,
            },
        ).execute()
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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/trends", response_model=TimeSeriesResponse)
async def get_agent_trends(
    time_range: TimeRangeParams = Depends(),
    agent_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
):
    sb = get_supabase_client()
    try:
        agent_filter = f" AND agent_type = '{agent_type}'" if agent_type else ""
        query = f"""
        SELECT 
            date_trunc('day', created_at) as date,
            (count(*) filter (where status = 'success')::numeric / nullif(count(*), 0)::numeric * 100) as value
        FROM agent_logs
        WHERE created_at BETWEEN '{time_range.start_date}' AND '{time_range.end_date}'{agent_filter}
        GROUP BY date
        ORDER BY date
        """
        result = sb.rpc("execute_sql", {"query": query}).execute()  # Adjust for actual method
        data_points = [
            TimeSeriesDataPoint(date=row["date"].date(), value=row["value"], label=None)
            for row in result.data
        ]
        return TimeSeriesResponse(
            data=data_points,
            metric_name="agent_success_rate_trends",
            aggregation="daily",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/logs")
async def get_agent_logs(
    pagination: PaginationParams = Depends(),
    filters: AnalyticsFilterParams = Depends(),
    current_user: dict = Depends(require_admin),
):
    sb = get_supabase_client()
    try:
        agent_type_filter = {"agent_type": {"eq": filters.agent_type}} if filters.agent_type else {}
        status_filter = {"status": {"eq": filters.status}} if filters.status else {}
        sort_by = filters.sort_by or "created_at"
        sort_order = filters.sort_order or "desc"
        query = sb.table("agent_logs").select("*").match({**agent_type_filter, **status_filter}).order(sort_by, desc=(sort_order == "desc")).limit(pagination.limit).offset(pagination.offset)
        result = query.execute()
        total_query = sb.table("agent_logs").select("id", count="exact").match({**agent_type_filter, **status_filter})
        total_result = total_query.execute()
        total = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        return {"items": result.data, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/services/recommendations", response_model=List[ServiceRecommendation])
async def get_service_recommendations(
    current_user: dict = Depends(get_current_user),
):
    sb = get_supabase_client()
    try:
        if current_user["role"] == "admin":
            result = sb.rpc("get_service_recommendations_insights").execute()
        else:
            result = sb.rpc("get_service_recommendations_insights_for_user", {"user_uuid": current_user["user_id"]}).execute()
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
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
