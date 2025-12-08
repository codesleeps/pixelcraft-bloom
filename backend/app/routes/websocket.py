from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import asyncio
import json
import sentry_sdk
import uuid
from ..utils.redis_client import subscribe_to_analytics_events
from ..utils.auth import verify_supabase_token
from ..utils.logger import logger
from ..utils.supabase_client import get_supabase_client
from ..utils.sentry_helpers import set_user_context, start_transaction

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
    """
    Real-time WebSocket connection for receiving analytics events and metrics updates.
    
    Provides real-time updates for:
    - Lead creation and analysis events
    - Conversation messages and deletions
    - Revenue and subscription changes
    - Agent logs and performance metrics
    
    Authentication: Requires valid Supabase JWT token as query parameter
    """
    connection_id = str(uuid.uuid4())
    # Authenticate the token
    try:
        payload = verify_supabase_token(token)
        user_id = payload.get("sub")
        if not user_id:
            sentry_sdk.capture_message("WebSocket authentication failed: no user_id", level="warning", extra={"connection_id": connection_id})
            await websocket.close(code=1008)
            return
        # Fetch role from user_profiles
        supabase = get_supabase_client()
        response = supabase.table("user_profiles").select("role").eq("user_id", user_id).execute()
        if not response.data:
            sentry_sdk.capture_message("WebSocket authentication failed: no user profile", level="warning", extra={"connection_id": connection_id, "user_id": user_id})
            await websocket.close(code=1008)
            return
        role = response.data[0]["role"]
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        sentry_sdk.capture_exception(e, extra={"connection_id": connection_id, "user_id": user_id if 'user_id' in locals() else None})
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)
    logger.info("WebSocket connection established for user %s", user_id)

    transaction = start_transaction(name="websocket.analytics", op="websocket.connection")

    # Determine channels
    if role == "admin":
        channels = ["analytics:leads", "analytics:conversations", "analytics:revenue", "analytics:agents", "analytics:workflows"]
    else:
        channels = [f"analytics:user:{user_id}"]

    sentry_sdk.set_context("websocket", {"connection_id": connection_id, "user_id": user_id, "role": role, "endpoint": "analytics", "channels": channels})
    set_user_context({"id": user_id, "role": role})
    sentry_sdk.add_breadcrumb(message="WebSocket connection opened", category="websocket", data={"endpoint": "analytics"})
    message_count = 0

    # Subscribe to channels
    pubsub = subscribe_to_analytics_events(channels)
    if pubsub is None:
        logger.warning("Redis unavailable for user %s, keeping connection idle", user_id)
        last_ping = asyncio.get_event_loop().time()
        try:
            while True:
                now = asyncio.get_event_loop().time()
                if now - last_ping >= 30:
                    sentry_sdk.add_breadcrumb(message="Heartbeat ping sent", category="websocket")
                    await websocket.send_json({"type": "ping"})
                    last_ping = now
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for user %s", user_id)
            sentry_sdk.add_breadcrumb(message="WebSocket disconnected", category="websocket")
        finally:
            manager.disconnect(user_id)
            sentry_sdk.add_breadcrumb(message="WebSocket connection closed", category="websocket")
            if transaction:
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("websocket", {"message_count": message_count})
                transaction.finish()
        return

    # Message forwarding loop
    last_ping = asyncio.get_event_loop().time()
    try:
        while True:
            now = asyncio.get_event_loop().time()
            if now - last_ping >= 30:
                sentry_sdk.add_breadcrumb(message="Heartbeat ping sent", category="websocket")
                await websocket.send_json({"type": "ping"})
                last_ping = now
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, pubsub.get_message, True, 1.0
                )
                if message and message.get('type') == 'message':
                    data = json.loads(message['data'])
                    sentry_sdk.add_breadcrumb(message="Message received from Redis", category="websocket", data={"channel": message.get('channel')})
                    await websocket.send_json(data)
                    sentry_sdk.add_breadcrumb(message="Message sent to client", category="websocket")
                    message_count += 1
            except Exception as e:
                logger.error("Error processing Redis message: %s", e)
                sentry_sdk.capture_exception(e)
                sentry_sdk.add_breadcrumb(message="Error processing Redis message", category="websocket", level="error")
                break
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user %s", user_id)
        sentry_sdk.add_breadcrumb(message="WebSocket disconnected", category="websocket")
    except Exception as e:
        logger.error("WebSocket error for user %s: %s", user_id, e)
        sentry_sdk.capture_exception(e)
        sentry_sdk.add_breadcrumb(message="WebSocket error occurred", category="websocket", level="error")
    finally:
        manager.disconnect(user_id)
        if pubsub:
            pubsub.unsubscribe()
            pubsub.close()
        sentry_sdk.add_breadcrumb(message="WebSocket connection closed", category="websocket")
        if transaction:
            with sentry_sdk.configure_scope() as scope:
                scope.set_context("websocket", {"message_count": message_count})
            transaction.finish()


@router.websocket("/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str, token: str = Query(...)):
    connection_id = str(uuid.uuid4())
    # Authenticate the token
    try:
        payload = verify_supabase_token(token)
        user_id = payload.get("sub")
        if not user_id:
            sentry_sdk.capture_message("WebSocket authentication failed: no user_id", level="warning", extra={"connection_id": connection_id, "workflow_id": workflow_id})
            await websocket.close(code=1008)
            return
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        sentry_sdk.capture_exception(e, extra={"connection_id": connection_id, "workflow_id": workflow_id, "user_id": user_id if 'user_id' in locals() else None})
        await websocket.close(code=1008)
        return

    # Verify access to workflow
    supabase = get_supabase_client()
    try:
        workflow_response = supabase.table("workflow_executions").select("conversation_id").eq("id", workflow_id).execute()
        if not workflow_response.data:
            sentry_sdk.capture_message("WebSocket access verification failed: workflow not found", level="warning", extra={"connection_id": connection_id, "workflow_id": workflow_id, "user_id": user_id})
            await websocket.close(code=1008)
            return
        conversation_id = workflow_response.data[0]["conversation_id"]
        conversation_response = supabase.table("conversations").select("user_id").eq("id", conversation_id).execute()
        if not conversation_response.data or conversation_response.data[0]["user_id"] != user_id:
            sentry_sdk.capture_message("WebSocket access verification failed: unauthorized", level="warning", extra={"connection_id": connection_id, "workflow_id": workflow_id, "user_id": user_id, "conversation_id": conversation_id})
            await websocket.close(code=1008)
            return
    except Exception as e:
        logger.error("Access verification failed: %s", e)
        sentry_sdk.capture_exception(e, extra={"connection_id": connection_id, "workflow_id": workflow_id, "user_id": user_id})
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)
    logger.info("Workflow WebSocket connection established for user %s, workflow %s", user_id, workflow_id)

    transaction = start_transaction(name="websocket.workflow", op="websocket.connection")

    sentry_sdk.set_context("websocket", {"connection_id": connection_id, "user_id": user_id, "endpoint": "workflow", "workflow_id": workflow_id})
    set_user_context({"id": user_id})
    sentry_sdk.add_breadcrumb(message="WebSocket connection opened", category="websocket", data={"endpoint": "workflow", "workflow_id": workflow_id})
    message_count = 0

    # Send initial workflow state
    try:
        workflow_data = supabase.table("workflow_executions").select("*").eq("id", workflow_id).execute()
        if workflow_data.data:
            initial_data = workflow_data.data[0]
            sentry_sdk.add_breadcrumb(message="Initial workflow state sent", category="websocket")
            await websocket.send_json({
                "type": "workflow_update",
                "workflow_id": workflow_id,
                "event_type": "initial_state",
                "data": initial_data,
                "timestamp": asyncio.get_event_loop().time()
            })
            message_count += 1
    except Exception as e:
        logger.error("Failed to send initial workflow state: %s", e)
        sentry_sdk.capture_exception(e)

    # Subscribe to workflow channel
    pubsub = subscribe_to_analytics_events([f"workflow:{workflow_id}"])
    if pubsub is None:
        logger.warning("Redis unavailable for workflow %s, keeping connection idle", workflow_id)
        last_ping = asyncio.get_event_loop().time()
        try:
            while True:
                now = asyncio.get_event_loop().time()
                if now - last_ping >= 30:
                    sentry_sdk.add_breadcrumb(message="Heartbeat ping sent", category="websocket")
                    await websocket.send_json({"type": "ping"})
                    last_ping = now
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            logger.info("Workflow WebSocket disconnected for user %s, workflow %s", user_id, workflow_id)
            sentry_sdk.add_breadcrumb(message="WebSocket disconnected", category="websocket")
        finally:
            manager.disconnect(user_id)
            sentry_sdk.add_breadcrumb(message="WebSocket connection closed", category="websocket")
            if transaction:
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("websocket", {"message_count": message_count})
                transaction.finish()
        return

    # Message forwarding loop
    last_ping = asyncio.get_event_loop().time()
    try:
        while True:
            now = asyncio.get_event_loop().time()
            if now - last_ping >= 30:
                sentry_sdk.add_breadcrumb(message="Heartbeat ping sent", category="websocket")
                await websocket.send_json({"type": "ping"})
                last_ping = now
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, pubsub.get_message, True, 1.0
                )
                if message and message.get('type') == 'message':
                    data = json.loads(message['data'])
                    sentry_sdk.add_breadcrumb(message="Message received from Redis", category="websocket", data={"channel": message.get('channel')})
                    await websocket.send_json({
                        "type": "workflow_update",
                        "workflow_id": workflow_id,
                        "event_type": data.get("event_type"),
                        "data": data.get("data"),
                        "timestamp": data.get("timestamp")
                    })
                    sentry_sdk.add_breadcrumb(message="Message sent to client", category="websocket")
                    message_count += 1
            except Exception as e:
                logger.error("Error processing Redis message: %s", e)
                sentry_sdk.capture_exception(e)
                sentry_sdk.add_breadcrumb(message="Error processing Redis message", category="websocket", level="error")
                break
    except WebSocketDisconnect:
        logger.info("Workflow WebSocket disconnected for user %s, workflow %s", user_id, workflow_id)
        sentry_sdk.add_breadcrumb(message="WebSocket disconnected", category="websocket")
    except Exception as e:
        logger.error("Workflow WebSocket error for user %s, workflow %s: %s", user_id, workflow_id, e)
        sentry_sdk.capture_exception(e)
        sentry_sdk.add_breadcrumb(message="WebSocket error occurred", category="websocket", level="error")
    finally:
        manager.disconnect(user_id)
        if pubsub:
            pubsub.unsubscribe()
            pubsub.close()
        sentry_sdk.add_breadcrumb(message="WebSocket connection closed", category="websocket")
        if transaction:
            with sentry_sdk.configure_scope() as scope:
                scope.set_context("websocket", {"message_count": message_count})
            transaction.finish()


@router.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket, token: str = Query(...)):
    connection_id = str(uuid.uuid4())
    # Authenticate the token
    try:
        payload = verify_supabase_token(token)
        user_id = payload.get("sub")
        if not user_id:
            sentry_sdk.capture_message("WebSocket authentication failed: no user_id", level="warning", extra={"connection_id": connection_id})
            await websocket.close(code=1008)
            return
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        sentry_sdk.capture_exception(e, extra={"connection_id": connection_id, "user_id": user_id if 'user_id' in locals() else None})
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)
    logger.info("Notifications WebSocket connection established for user %s", user_id)

    transaction = start_transaction(name="websocket.notifications", op="websocket.connection")

    sentry_sdk.set_context("websocket", {"connection_id": connection_id, "user_id": user_id, "endpoint": "notifications", "channels": [f"notifications:user:{user_id}"]})
    set_user_context({"id": user_id})
    sentry_sdk.add_breadcrumb(message="WebSocket connection opened", category="websocket", data={"endpoint": "notifications"})
    message_count = 0

    # Subscribe to user-specific notification channel
    pubsub = subscribe_to_analytics_events([f"notifications:user:{user_id}"])
    if pubsub is None:
        logger.warning("Redis unavailable for user %s, keeping connection idle", user_id)
        last_ping = asyncio.get_event_loop().time()
        try:
            while True:
                now = asyncio.get_event_loop().time()
                if now - last_ping >= 30:
                    sentry_sdk.add_breadcrumb(message="Heartbeat ping sent", category="websocket")
                    await websocket.send_json({"type": "ping"})
                    last_ping = now
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            logger.info("Notifications WebSocket disconnected for user %s", user_id)
            sentry_sdk.add_breadcrumb(message="WebSocket disconnected", category="websocket")
        finally:
            manager.disconnect(user_id)
            sentry_sdk.add_breadcrumb(message="WebSocket connection closed", category="websocket")
            if transaction:
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("websocket", {"message_count": message_count})
                transaction.finish()
        return

    # Message forwarding loop
    last_ping = asyncio.get_event_loop().time()
    try:
        while True:
            now = asyncio.get_event_loop().time()
            if now - last_ping >= 30:
                sentry_sdk.add_breadcrumb(message="Heartbeat ping sent", category="websocket")
                await websocket.send_json({"type": "ping"})
                last_ping = now
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, pubsub.get_message, True, 1.0
                )
                if message and message.get('type') == 'message':
                    data = json.loads(message['data'])
                    sentry_sdk.add_breadcrumb(message="Message received from Redis", category="websocket", data={"channel": message.get('channel')})
                    await websocket.send_json(data)
                    sentry_sdk.add_breadcrumb(message="Message sent to client", category="websocket")
                    message_count += 1
            except Exception as e:
                logger.error("Error processing Redis message: %s", e)
                sentry_sdk.capture_exception(e)
                sentry_sdk.add_breadcrumb(message="Error processing Redis message", category="websocket", level="error")
                break
    except WebSocketDisconnect:
        logger.info("Notifications WebSocket disconnected for user %s", user_id)
        sentry_sdk.add_breadcrumb(message="WebSocket disconnected", category="websocket")
    except Exception as e:
        logger.error("Notifications WebSocket error for user %s: %s", user_id, e)
        sentry_sdk.capture_exception(e)
        sentry_sdk.add_breadcrumb(message="WebSocket error occurred", category="websocket", level="error")
    finally:
        manager.disconnect(user_id)
        if pubsub:
            pubsub.unsubscribe()
            pubsub.close()
        sentry_sdk.add_breadcrumb(message="WebSocket connection closed", category="websocket")
        if transaction:
            with sentry_sdk.configure_scope() as scope:
                scope.set_context("websocket", {"message_count": message_count})
            transaction.finish()
