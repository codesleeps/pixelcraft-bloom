from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from ..models.lead import LeadRequest, LeadResponse, LeadAnalysis, LeadScore
from ..utils.supabase_client import get_supabase_client
from ..utils.redis_client import publish_analytics_event

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/submit", response_model=LeadResponse)
async def submit_lead(req: LeadRequest):
    # Insert lead into Supabase and optionally run analysis
    lead_id = str(uuid4())
    sb = get_supabase_client()
    try:
        _ = sb.table("leads").insert({"id": lead_id, **req.lead_data.dict()}).execute()
    except Exception:
        # Fail gracefully but raise for now
        raise HTTPException(status_code=500, detail="Failed to store lead")

    # Publish analytics event for lead creation
    try:
        publish_analytics_event("analytics:leads", "lead_created", {"lead_id": lead_id, "user_id": req.lead_data.dict().get("user_id")})
    except Exception:
        # Log warning but don't fail the request if Redis is unavailable
        pass

    analysis = None
    if req.analyze:
        # Placeholder analysis — to be replaced by AgentScope lead qualification
        score = LeadScore(score=50, confidence=0.6, factors={"message_length": 0.5}, priority="medium")
        analysis = LeadAnalysis(lead_score=score, recommended_services=["SEO"], key_insights=["No company provided"], suggested_actions=["Follow up via email"], estimated_value=None)

    return LeadResponse(lead_id=lead_id, analysis=analysis, status="received")


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    sb = get_supabase_client()
    try:
        res = sb.table("leads").select("*").eq("id", lead_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return res.data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve lead")


@router.get("")
async def list_leads(limit: int = 50, offset: int = 0):
    sb = get_supabase_client()
    try:
        res = sb.table("leads").select("*").limit(limit).offset(offset).execute()
        return {"items": res.data or [], "total": len(res.data or [])}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list leads")



@router.post("/{lead_id}/analyze", response_model=LeadAnalysis)
async def analyze_lead(lead_id: str):
    """Re-run AI analysis on an existing lead and update stored analysis.

    This is a placeholder that returns a canned analysis. In the next phase this will invoke the Lead Qualification Agent.
    """
    sb = get_supabase_client()
    try:
        res = sb.table("leads").select("*").eq("id", lead_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Lead not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve lead for analysis")

    # Placeholder scoring logic
    score = LeadScore(score=75, confidence=0.85, factors={"message_length": 0.2, "email_domain": 0.3}, priority="high")
    analysis = LeadAnalysis(lead_score=score, recommended_services=["SEO","Strategy"], key_insights=["Good budget indicated"], suggested_actions=["Schedule discovery call"], estimated_value=None)

    # Save analysis to Supabase agent_logs or leads.analysis column (schema-dependent)
    try:
        _ = sb.table("agent_logs").insert({"lead_id": lead_id, "analysis": analysis.dict()}).execute()
    except Exception:
        # Ignore persistence errors for now
        pass

    # Publish analytics event for lead analysis
    try:
        publish_analytics_event("analytics:leads", "lead_analyzed", {"lead_id": lead_id})
    except Exception:
        # Log warning but don't fail the request if Redis is unavailable
        pass

    return analysis
