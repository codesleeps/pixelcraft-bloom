import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.main import app
from app.routes.websocket import router

client = TestClient(app)

@pytest.fixture
def mock_auth():
    with patch("app.routes.websocket.verify_supabase_token") as mock:
        mock.return_value = {"sub": "test-user-id", "role": "user"}
        yield mock

@pytest.fixture
def mock_redis_pubsub():
    with patch("app.routes.websocket.subscribe_to_analytics_events") as mock:
        pubsub_mock = MagicMock()
        mock.return_value = pubsub_mock
        
        # Mock get_message to return a message once then None (or block)
        # We'll simulate receiving one message
        async def mock_get_message(*args, **kwargs):
            return {
                "type": "message",
                "channel": "notifications:user:test-user-id",
                "data": json.dumps({
                    "event_type": "notification_created",
                    "notification": {"id": "123", "title": "Test Notification"}
                })
            }
        
        # In a real loop, we'd need to handle multiple calls. 
        # For TestClient websocket, it runs in the same thread/loop usually, 
        # but here we are mocking the pubsub which is called inside the endpoint.
        # The endpoint runs an infinite loop. We need to break it or let it run.
        # TestClient.websocket_connect context manager handles the connection.
        
        # To avoid infinite loop in test, we can make get_message raise an exception after first call
        # or we can rely on client.disconnect() to break the loop if the endpoint checks for disconnect.
        
        pubsub_mock.get_message = MagicMock(side_effect=[
            {
                "type": "message",
                "channel": "notifications:user:test-user-id",
                "data": json.dumps({
                    "event_type": "notification_created",
                    "notification": {"id": "123", "title": "Test Notification"}
                })
            },
            Exception("Break loop") # Raise exception to break the while True loop
        ])
        
        yield pubsub_mock

def test_notifications_websocket(mock_auth, mock_redis_pubsub):
    with client.websocket_connect("/api/ws/notifications?token=valid-token") as websocket:
        # Receive the message we mocked
        data = websocket.receive_json()
        assert data["event_type"] == "notification_created"
        assert data["notification"]["title"] == "Test Notification"
        
        # Receive ping (the loop sends ping every 30s, but we might not wait that long)
        # We can close the connection
        websocket.close()
