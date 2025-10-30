from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import asyncio
import json
from ..utils.redis_client import subscribe_to_analytics_events
from ..utils.auth import verify_supabase_token
from ..utils.logger import logger
from ..utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    def get_connection(self, user_id: str) -> WebSocket | None:
        return self.active_connections.get(user_id)

manager = ConnectionManager()

@router.websocket("/analytics")
async def analytics_websocket(websocket: WebSocket, token: str = Query(...)):
    # Authenticate the token
    try:
        payload = verify_supabase_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008)
            return
        # Fetch role from user_profiles
        supabase = get_supabase_client()
        response = supabase.table("user_profiles").select("role").eq("user_id", user_id).execute()
        if not response.data:
            await websocket.close(code=1008)
            return
        role = response.data[0]["role"]
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)
    logger.info("WebSocket connection established for user %s", user_id)

    # Determine channels
    if role == "admin":
        channels = ["analytics:leads", "analytics:conversations", "analytics:revenue", "analytics:agents"]
    else:
        channels = [f"analytics:user:{user_id}"]

    # Subscribe to channels
    pubsub = subscribe_to_analytics_events(channels)
    if pubsub is None:
        logger.warning("Redis unavailable for user %s, keeping connection idle", user_id)
        last_ping = asyncio.get_event_loop().time()
        try:
            while True:
                now = asyncio.get_event_loop().time()
                if now - last_ping >= 30:
                    await websocket.send_json({"type": "ping"})
                    last_ping = now
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for user %s", user_id)
        finally:
            manager.disconnect(user_id)
        return

    # Message forwarding loop
    last_ping = asyncio.get_event_loop().time()
    try:
        while True:
            now = asyncio.get_event_loop().time()
            if now - last_ping >= 30:
                await websocket.send_json({"type": "ping"})
                last_ping = now
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, pubsub.get_message, True, 1.0
                )
                if message and message.get('type') == 'message':
                    data = json.loads(message['data'])
                    await websocket.send_json(data)
            except Exception as e:
                logger.error("Error processing Redis message: %s", e)
                break
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user %s", user_id)
    except Exception as e:
        logger.error("WebSocket error for user %s: %s", user_id, e)
    finally:
        manager.disconnect(user_id)
        if pubsub:
            pubsub.unsubscribe()
            pubsub.close()