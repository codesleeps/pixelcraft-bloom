from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from ..models.lead import LeadRequest, LeadResponse, LeadAnalysis, LeadScore, LeadUpdate
from ..utils.supabase_client import get_supabase_client
from ..utils.redis_client import publish_analytics_event
from ..utils.notification_service import create_notification, create_notification_for_admins
from ..utils.external_tools import send_email
from ..agents.lead_agent import create_lead_qualification_agent
from ..routes.models import get_model_manager
from ..models.manager import ModelManager

router = APIRouter(prefix="/leads", tags=["leads"])


@router.patch("/{lead_id}", response_model=LeadResponse, summary="Update lead information", description="Update specific fields of an existing lead record, such as status, assignment, or notes.")
async def update_lead(lead_id: str, update: LeadUpdate):
    sb = get_supabase_client()
    
    # Prepare update data
    update_data = {}
    if update.status:
        update_data["status"] = update.status
    if update.assigned_to:
        update_data["assigned_to"] = update.assigned_to
    if update.metadata:
        update_data["metadata"] = update.metadata
        
    # Handle notes separately (append to metadata for now)
    if update.notes:
        # Fetch current metadata first
        try:
            current = sb.table("leads").select("metadata").eq("id", lead_id).single().execute()
            current_metadata = current.data.get("metadata") or {}
            existing_notes = current_metadata.get("notes", [])
            
            # Create new note object
            new_note = {
                "content": update.notes,
                "created_at": datetime.utcnow().isoformat(),
                # "created_by": current_user.id  # TODO: Add auth context to get user ID
            }
            existing_notes.append(new_note)
            
            # Update metadata in update_data
            if "metadata" not in update_data:
                update_data["metadata"] = current_metadata
            update_data["metadata"]["notes"] = existing_notes
            
        except Exception as e:
            # Log error but proceed with other updates
            print(f"Failed to fetch existing metadata for notes: {e}")

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
        
    try:
        res = sb.table("leads").update(update_data).eq("id", lead_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Lead not found")
            
        # Publish event
        try:
            publish_analytics_event("analytics:leads", "lead_updated", {"lead_id": lead_id, "updates": update_data})
        except Exception:
            pass
            
        # Notify assignee if assigned_to changed
        if update.assigned_to:
            try:
                await create_notification(
                    recipient_id=update.assigned_to,
                    notification_type="lead",
                    severity="info",
                    title="Lead Assigned",
                    message=f"You have been assigned lead {lead_id}",
                    action_url=f"/dashboard/leads/{lead_id}",
                    metadata={"lead_id": lead_id}
                )
            except Exception:
                pass
                
        return LeadResponse(
            lead_id=lead_id, 
            status=res.data[0].get("status", "received"), 
            created_at=res.data[0].get("created_at")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lead: {str(e)}")



@router.post("/submit", response_model=LeadResponse, summary="Submit a new lead", description="Create a new lead with optional AI-powered qualification analysis and scoring.")
async def submit_lead(req: LeadRequest, mm: Optional[ModelManager] = Depends(get_model_manager)):
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

    # Create notification for lead creation
    try:
        user_id = req.lead_data.dict().get("user_id")
        if user_id:
            await create_notification(
                recipient_id=user_id,
                notification_type="lead",
                severity="success",
                title="New Lead Created",
                message=f"Lead {lead_id} has been successfully created",
                action_url=f"/dashboard/leads/{lead_id}",
                metadata={"lead_id": lead_id}
            )
        else:
            await create_notification_for_admins(
                notification_type="lead",
                severity="success",
                title="New Lead Created",
                message=f"Lead {lead_id} has been successfully created",
                action_url=f"/dashboard/leads/{lead_id}",
                metadata={"lead_id": lead_id}
            )
    except Exception:
        # Log warning but don't fail the request if notification creation fails
        pass

    analysis = None
    if req.analyze:
        if mm:
            try:
                agent = create_lead_qualification_agent(mm)
                # We need to adapt the call because process_message expects a message string
                # But LeadQualificationAgent.process_message logic handles metadata["lead_data"]
                message = f"Analyze lead: {req.lead_data.company or 'Unknown Company'}"
                
                response = await agent.process_message(
                    conversation_id=lead_id,
                    message=message,
                    metadata={"lead_data": req.lead_data.dict()}
                )
                
                analysis_dict = response.metadata
                
                # Convert list of reasons to dict for factors
                factors = {}
                for reason in analysis_dict.get("heuristic_reasons", []):
                    factors[reason] = 1.0
                
                score = LeadScore(
                    score=int(analysis_dict.get("score", 0)),
                    confidence=float(analysis_dict.get("confidence", 0.0)),
                    factors=factors,
                    priority=analysis_dict.get("priority", "medium")
                )
                
                analysis = LeadAnalysis(
                    lead_score=score,
                    recommended_services=analysis_dict.get("recommended_services", []),
                    key_insights=analysis_dict.get("key_insights", []),
                    suggested_actions=analysis_dict.get("suggested_actions", []),
                    estimated_value=float(analysis_dict.get("estimated_value")) if analysis_dict.get("estimated_value") else None
                )
            except Exception as e:
                # Log error
                print(f"Agent analysis failed: {e}")
                # Fallback
                score = LeadScore(score=50, confidence=0.5, factors={"error": 1.0}, priority="medium")
                analysis = LeadAnalysis(lead_score=score, recommended_services=[], key_insights=["Analysis failed"], suggested_actions=[], estimated_value=None)
        else:
            # Fallback if ModelManager is not available
            score = LeadScore(score=50, confidence=0.6, factors={"message_length": 0.5}, priority="medium")
            analysis = LeadAnalysis(lead_score=score, recommended_services=["SEO"], key_insights=["No company provided"], suggested_actions=["Follow up via email"], estimated_value=None)

    return LeadResponse(lead_id=lead_id, analysis=analysis, status="received")


@router.get("/{lead_id}", summary="Retrieve lead details", description="Get detailed information about a specific lead by its ID.")
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


@router.get("", summary="List leads", description="Retrieve a paginated list of leads with optional filtering by status, assignment, and search query.")
async def list_leads(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    search: Optional[str] = None
):
    sb = get_supabase_client()
    try:
        query = sb.table("leads").select("*", count="exact")
        
        if status:
            query = query.eq("status", status)
        if assigned_to:
            query = query.eq("assigned_to", assigned_to)
        if search:
            # Simple search on name, email, or company
            # Supabase 'or' syntax: "name.ilike.%query%,email.ilike.%query%..."
            search_filter = f"name.ilike.%{search}%,email.ilike.%{search}%,company.ilike.%{search}%"
            query = query.or_(search_filter)
            
        # Order by created_at desc by default
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        
        res = query.execute()
        return {"items": res.data or [], "total": res.count}
    except Exception as e:
        print(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to list leads")


@router.post("/{lead_id}/analyze", response_model=LeadAnalysis, summary="Analyze existing lead", description="Run AI-powered analysis on an existing lead to generate qualification score, insights, and recommendations.")
async def analyze_lead(lead_id: str, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Re-run AI analysis on an existing lead and update stored analysis."""
    sb = get_supabase_client()
    try:
        res = sb.table("leads").select("*").eq("id", lead_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead_data = res.data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve lead for analysis")

    if mm:
        try:
            agent = create_lead_qualification_agent(mm)
            message = f"Analyze lead: {lead_data.get('company') or 'Unknown Company'}"
            response = await agent.process_message(
                conversation_id=lead_id,
                message=message,
                metadata={"lead_data": lead_data}
            )
            
            analysis_dict = response.metadata
            
            factors = {}
            for reason in analysis_dict.get("heuristic_reasons", []):
                factors[reason] = 1.0
            
            score = LeadScore(
                score=int(analysis_dict.get("score", 0)),
                confidence=float(analysis_dict.get("confidence", 0.0)),
                factors=factors,
                priority=analysis_dict.get("priority", "medium")
            )
            
            analysis = LeadAnalysis(
                lead_score=score,
                recommended_services=analysis_dict.get("recommended_services", []),
                key_insights=analysis_dict.get("key_insights", []),
                suggested_actions=analysis_dict.get("suggested_actions", []),
                estimated_value=float(analysis_dict.get("estimated_value")) if analysis_dict.get("estimated_value") else None
            )
            
            # Save analysis to Supabase agent_logs or leads.analysis column (schema-dependent)
            try:
                _ = sb.table("agent_logs").insert({"lead_id": lead_id, "analysis": analysis.dict()}).execute()
                # Also update the lead record itself if possible
                _ = sb.table("leads").update({"lead_score": score.score, "metadata": {"last_analysis": analysis.dict()}}).eq("id", lead_id).execute()
            except Exception:
                # Ignore persistence errors for now
                pass

            # Publish analytics event for lead analysis
            try:
                publish_analytics_event("analytics:leads", "lead_analyzed", {"lead_id": lead_id})
            except Exception:
                pass

            # Create notification for lead analysis
            try:
                user_id = lead_data.get("user_id")
                if user_id:
                    await create_notification(
                        recipient_id=user_id,
                        notification_type="lead",
                        severity="info",
                        title="Lead Analysis Complete",
                        message=f"Lead {lead_id} has been analyzed with score {score.score}",
                        action_url=f"/dashboard/leads/{lead_id}",
                        metadata={"lead_id": lead_id, "score": score.score}
                    )
            except Exception:
                pass
                
        except Exception as e:
             # Log error
            print(f"Agent analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Agent analysis failed: {e}")
    else:
        # Fallback
        score = LeadScore(score=75, confidence=0.85, factors={"message_length": 0.2, "email_domain": 0.3}, priority="high")
        analysis = LeadAnalysis(lead_score=score, recommended_services=["SEO","Strategy"], key_insights=["Good budget indicated"], suggested_actions=["Schedule discovery call"], estimated_value=None)

    return analysis
