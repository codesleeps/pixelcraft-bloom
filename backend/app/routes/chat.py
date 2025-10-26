from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List
import json
import time

from ..models.chat import ChatRequest, ChatResponse, ChatStreamChunk, ChatMessage
from ..config import settings
from ..utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def post_message(req: ChatRequest):
    """Handle a chat message and return a single aggregated response."""
    # Placeholder orchestration: call AgentOrchestrator in next phase
    # For now, echo back a canned response and store message in Supabase if configured
    conversation_id = req.conversation_id or f"conv_{int(time.time())}"

    # Store message in supabase conversations table if available
    try:
        sb = get_supabase_client()
        # Soft attempt to insert message (table schema to be created in DB)
        _ = sb.table("conversations").insert({"conversation_id": conversation_id, "role": "user", "content": req.message}).execute()
    except Exception:
        # Suppress DB errors for now; real errors should be logged
        pass

    resp = ChatResponse(response=f"Echo: {req.message}", conversation_id=conversation_id, agent_type="chat")
    return resp


def _sse_generator(message: str):
    # Very small streaming simulation yielding chunks
    for i in range(0, len(message), 40):
        chunk = message[i : i + 40]
        payload = ChatStreamChunk(chunk=chunk, done=(i + 40 >= len(message))).dict()
        yield json.dumps(payload) + "\n"
        time.sleep(0.01)


@router.post("/stream")
async def post_stream(req: ChatRequest):
    """Return a streaming response (SSE-like simple implementation).

    The frontend can consume this chunked JSON stream. Replace with proper EventSourceResponse in production.
    """
    message = f"Streaming reply for: {req.message}"
    return StreamingResponse(_sse_generator(message), media_type="application/json")


@router.get("/history/{conversation_id}", response_model=List[ChatMessage])
async def get_history(conversation_id: str, limit: int = 50, offset: int = 0):
    try:
        sb = get_supabase_client()
        res = sb.table("conversations").select("role,content,timestamp").eq("conversation_id", conversation_id).order("timestamp", desc=False).limit(limit).offset(offset).execute()
        rows = res.data or []
        messages = [ChatMessage(role=r.get("role", "user"), content=r.get("content", ""), timestamp=r.get("timestamp")) for r in rows]
        return messages
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.delete("/history/{conversation_id}")
async def delete_history(conversation_id: str):
    try:
        sb = get_supabase_client()
        # Soft delete: set deleted_at timestamp (client SQL must have deleted_at column)
        _ = sb.table("conversations").update({"deleted_at": "now()"}).eq("conversation_id", conversation_id).execute()
        return JSONResponse(status_code=200, content={"deleted": True})
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete history")
