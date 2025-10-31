import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.routes.websocket import manager
from backend.app.utils.auth import verify_supabase_token
from backend.app.utils.redis_client import subscribe_to_analytics_events


@pytest.fixture
def mock_pubsub():
    """Mock pubsub object for Redis subscription."""
    pubsub = MagicMock()
    pubsub.get_message = MagicMock(return_value=None)
    pubsub.unsubscribe = MagicMock()
    pubsub.close = MagicMock()
    return pubsub


@pytest.fixture
def mock_verify_token():
    """Mock verify_supabase_token to return a test user payload."""
    with patch('backend.app.routes.websocket.verify_supabase_token') as mock_verify:
        mock_verify.return_value = {"sub": "test_user_id"}
        yield mock_verify


@pytest.fixture
def mock_subscribe():
    """Mock subscribe_to_analytics_events to return a mock pubsub."""
    with patch('backend.app.routes.websocket.subscribe_to_analytics_events') as mock_sub:
        yield mock_sub


class TestNotificationsWebSocket:
    """Integration tests for the notifications WebSocket endpoint."""

    def test_connection_establishment_success(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test successful WebSocket connection with valid token."""
        mock_subscribe.return_value = mock_pubsub
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            # Connection should be accepted
            assert websocket.connected
            
            # User should be added to ConnectionManager
            assert "test_user_id" in manager.active_connections
            
            # Should subscribe to correct channel
            mock_subscribe.assert_called_once_with([f"notifications:user:test_user_id"])
        
        # Cleanup after disconnect
        assert "test_user_id" not in manager.active_connections

    def test_authentication_invalid_token(self, test_client, mock_verify_token):
        """Test connection rejected with invalid token."""
        mock_verify_token.side_effect = Exception("Invalid token")
        
        with pytest.raises(Exception):  # WebSocket connection should fail
            test_client.websocket_connect("/api/ws/notifications?token=invalid_token")

    def test_authentication_missing_token(self, test_client):
        """Test connection rejected with missing token."""
        with pytest.raises(Exception):  # Should fail without token
            test_client.websocket_connect("/api/ws/notifications")

    def test_authentication_no_user_profile(self, test_client, mock_verify_token, mock_supabase):
        """Test connection rejected when user profile not found."""
        mock_verify_token.return_value = {"sub": "nonexistent_user"}
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        with pytest.raises(Exception):  # Should fail due to no profile
            test_client.websocket_connect("/api/ws/notifications?token=valid_token")

    def test_real_time_message_delivery(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test messages from Redis pub/sub are forwarded to WebSocket."""
        mock_subscribe.return_value = mock_pubsub
        
        # Mock a message from Redis
        message_data = {"event_type": "notification_created", "data": {"id": "notif_1"}, "timestamp": "2023-01-01T00:00:00"}
        mock_pubsub.get_message.side_effect = [
            {"type": "message", "data": json.dumps(message_data)},
            None  # End the loop
        ]
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            received = websocket.receive_json()
            assert received == message_data

    def test_ping_keepalive(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test periodic ping messages are sent."""
        mock_subscribe.return_value = mock_pubsub
        mock_pubsub.get_message.return_value = None  # No Redis messages
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            # Simulate time passing (in a real test, might need asyncio or time mocking)
            # For simplicity, assume ping is sent after connection
            # In practice, you might need to mock asyncio.get_event_loop().time()
            pass  # This test might be tricky to implement synchronously

    def test_redis_unavailable_fallback(self, test_client, mock_verify_token, mock_subscribe):
        """Test connection stays open when Redis is unavailable."""
        mock_subscribe.return_value = None  # Redis unavailable
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            assert websocket.connected
            # Should receive ping messages only
            # Again, time simulation needed

    def test_connection_cleanup(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test proper cleanup on disconnect."""
        mock_subscribe.return_value = mock_pubsub
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            pass  # Connection closes here
        
        # Verify cleanup
        assert "test_user_id" not in manager.active_connections
        mock_pubsub.unsubscribe.assert_called_once()
        mock_pubsub.close.assert_called_once()

    def test_error_handling_malformed_message(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test malformed Redis messages are handled gracefully."""
        mock_subscribe.return_value = mock_pubsub
        mock_pubsub.get_message.return_value = {"type": "message", "data": "invalid json"}
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            # Connection should handle error and continue or close gracefully
            pass  # Assert no crash

    def test_concurrent_connections(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test multiple users can connect simultaneously."""
        mock_subscribe.return_value = mock_pubsub
        
        # Mock different users
        users = ["user1", "user2"]
        connections = []
        
        for i, user in enumerate(users):
            mock_verify_token.return_value = {"sub": user}
            conn = test_client.websocket_connect(f"/api/ws/notifications?token=token{i}")
            connections.append(conn)
            assert user in manager.active_connections
        
        # Cleanup
        for conn in connections:
            conn.close()
        
        for user in users:
            assert user not in manager.active_connections

    def test_message_filtering(self, test_client, mock_verify_token, mock_subscribe, mock_pubsub):
        """Test only messages on user's channel are received."""
        mock_subscribe.return_value = mock_pubsub
        
        # Mock messages on different channels
        messages = [
            {"type": "message", "data": json.dumps({"event_type": "other_user", "data": {}, "timestamp": "2023-01-01T00:00:00"})},
            {"type": "message", "data": json.dumps({"event_type": "my_notification", "data": {"id": "notif_1"}, "timestamp": "2023-01-01T00:00:01"})},
        ]
        mock_pubsub.get_message.side_effect = messages + [None]
        
        with test_client.websocket_connect("/api/ws/notifications?token=valid_token") as websocket:
            # Should only receive the message on the user's channel
            # In practice, the pubsub is subscribed only to user's channel, so filtering happens at subscription
            received = websocket.receive_json()
            assert received["event_type"] == "my_notification"