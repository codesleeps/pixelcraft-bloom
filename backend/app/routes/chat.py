from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
import json
import time
import logging
import sentry_sdk
  
from ..models.chat import ChatRequest, ChatResponse, ChatStreamChunk, ChatMessage
from ..config import settings
from ..utils.supabase_client import get_supabase_client
from ..utils.redis_client import publish_analytics_event
from ..utils.notification_service import create_notification
from ..agents.chat_agent import create_chat_agent
from ..utils.limiter import limiter
  
logger = logging.getLogger("pixelcraft.routes.chat")
  
router = APIRouter(prefix="/chat", tags=["chat"])
  
  
@router.post("/message", response_model=ChatResponse)
@limiter.limit("100/minute")
async def post_message(req: ChatRequest, request: Request, model: Optional[str] = Query(None, description="Optional model to use for generation")):
    """Handle a chat message and return a single aggregated response using ChatAgent with ModelManager."""
    conversation_id = req.conversation_id or f"conv_{int(time.time())}"
      
    # Prepare metadata with optional model selection
    metadata = req.context or {}
    if model:
        metadata["model"] = model
      
    sentry_sdk.add_breadcrumb(category="chat", message="Message received", data={"conversation_id": conversation_id})
    sentry_sdk.set_context("chat_context", {"conversation_id": conversation_id, "message_length": len(req.message), "model": model, "metadata": metadata})
      
    try:
        # Create ChatAgent instance (integrates ModelManager)
        agent = create_chat_agent()
          
        sentry_sdk.add_breadcrumb(category="chat", message="Agent processing started")
          
        # Process message using agent (which uses ModelManager)
        agent_response = await agent.process_message(conversation_id, req.message, metadata)
          
        # Store message in Supabase conversations table if available
        try:
            sb = get_supabase_client()
            # Soft attempt to insert message (table schema to be created in DB)
            _ = sb.table("conversations").insert({"conversation_id": conversation_id, "role": "user", "content": req.message}).execute()
            sentry_sdk.add_breadcrumb(category="chat", message="Database insert completed")
            try:
                publish_analytics_event("analytics:conversations", "message_created", {"conversation_id": conversation_id})
            except Exception:
                pass
            try:
                conv = sb.table("conversations").select("user_id").eq("session_id", conversation_id).single().execute()
                user_id = conv.data.get("user_id")
                if user_id:
                    sentry_sdk.set_user({"id": user_id})
                    msg_count = sb.table("conversations").select("id", count="exact").eq("conversation_id", conversation_id).execute()
                    if msg_count.count == 1:
                        await create_notification(
                            recipient_id=user_id,
                            notification_type="conversation",
                            severity="info",
                            title="New Conversation Started",
                            message="A new conversation has been initiated",
                            action_url=f"/dashboard/conversations/{conversation_id}",
                            metadata={"conversation_id": conversation_id}
                        )
            except Exception:
                pass
        except Exception:
            # Suppress DB errors for now; real errors should be logged
            pass
          
        sentry_sdk.add_breadcrumb(category="chat", message="Response generated")
          
        # Return response with model metadata from agent
        resp = ChatResponse(
            response=agent_response.content,
            conversation_id=conversation_id,
            agent_type=agent_response.agent_id,
            metadata=agent_response.metadata
        )
        return resp
          
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Model processing failed: {str(e)}")
  
  
def _sse_generator(message: str):
    # Very small streaming simulation yielding chunks (integrate with agent response in future for true streaming)
    try:
        for i in range(0, len(message), 40):
            chunk = message[i : i + 40]
            payload = ChatStreamChunk(chunk=chunk, done=(i + 40 >= len(message))).dict()
            yield json.dumps(payload) + "\n"
            time.sleep(0.01)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        # Yield an error chunk if possible, but since ChatStreamChunk may not have error, just capture
  
  
@router.post("/stream")
@limiter.limit("100/minute")
async def post_stream(req: ChatRequest, request: Request, model: Optional[str] = Query(None, description="Optional model to use for generation")):
    """Return a streaming response (SSE-like simple implementation) using ChatAgent with ModelManager.
  
    The frontend can consume this chunked JSON stream. Replace with proper EventSourceResponse in production.
    """
    conversation_id = req.conversation_id or f"conv_{int(time.time())}"
      
    # Prepare metadata with optional model selection
    metadata = req.context or {}
    if model:
        metadata["model"] = model
      
    sentry_sdk.add_breadcrumb(category="chat", message="Stream message received", data={"conversation_id": conversation_id})
    sentry_sdk.set_context("chat_context", {"conversation_id": conversation_id, "message_length": len(req.message), "model": model, "metadata": metadata})
      
    try:
        # Create ChatAgent instance (integrates ModelManager)
        agent = create_chat_agent()
          
        sentry_sdk.add_breadcrumb(category="chat", message="Agent processing started for stream")
          
        # Process message using agent (which uses ModelManager) - for now, simulate streaming on response
        agent_response = await agent.process_message(conversation_id, req.message, metadata)
        message = agent_response.content
          
        sentry_sdk.add_breadcrumb(category="chat", message="Stream response generated")
          
        return StreamingResponse(_sse_generator(message), media_type="application/json")
          
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(f"Error processing streaming chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Model streaming failed: {str(e)}")
  
  
@router.get("/history/{conversation_id}", response_model=List[ChatMessage])
async def get_history(conversation_id: str, limit: int = 50, offset: int = 0):
    sentry_sdk.set_context("chat_context", {"conversation_id": conversation_id, "limit": limit, "offset": offset})
    try:
        sb = get_supabase_client()
        res = sb.table("conversations").select("role,content,timestamp").eq("conversation_id", conversation_id).order("timestamp", desc=False).limit(limit).offset(offset).execute()
        rows = res.data or []
        messages = [ChatMessage(role=r.get("role", "user"), content=r.get("content", ""), timestamp=r.get("timestamp")) for r in rows]
        return messages
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Failed to fetch history")
  
  
@router.delete("/history/{conversation_id}")
async def delete_history(conversation_id: str):
    sentry_sdk.set_context("chat_context", {"conversation_id": conversation_id})
    try:
        sb = get_supabase_client()
        # Soft delete: set deleted_at timestamp (client SQL must have deleted_at column)
        _ = sb.table("conversations").update({"deleted_at": "now()"}).eq("conversation_id", conversation_id).execute()
        try:
            publish_analytics_event("analytics:conversations", "conversation_deleted", {"conversation_id": conversation_id})
        except Exception:
            pass
        return JSONResponse(status_code=200, content={"deleted": True})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Failed to delete history")
