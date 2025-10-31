import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from backend.app.main import app
from backend.app.utils.supabase_client import get_supabase_client
from backend.app.utils.redis_client import get_redis_client, publish_analytics_event
from backend.app.utils.auth import get_current_user


@pytest.fixture
def test_client():
    """Returns FastAPI TestClient instance for making HTTP requests to the app without running a server."""
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock the get_supabase_client function to return a mock Supabase client with chainable query builder methods."""
    mock_client = MagicMock()
    
    # Create a mock table that supports chaining
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.is_.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.offset.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[])
    
    mock_client.table.return_value = mock_table
    
    with patch('backend.app.utils.supabase_client.get_supabase_client', return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_redis():
    """Mock the get_redis_client and publish_analytics_event functions to prevent actual Redis connections."""
    published_events = []
    
    def mock_publish(channel, event_type, data):
        published_events.append({'channel': channel, 'event_type': event_type, 'data': data})
    
    with patch('backend.app.utils.redis_client.get_redis_client', return_value=None), \
         patch('backend.app.utils.redis_client.publish_analytics_event', side_effect=mock_publish):
        yield published_events


@pytest.fixture
def mock_auth_user():
    """Mock the get_current_user dependency to return a test user dict."""
    test_user = {
        "user_id": "test_user_id",
        "role": "user",
        "metadata": {}
    }
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield test_user


@pytest.fixture
def mock_auth_admin():
    """Mock the get_current_user dependency to return a test admin dict."""
    test_admin = {
        "user_id": "test_admin_id",
        "role": "admin",
        "metadata": {}
    }
    app.dependency_overrides[get_current_user] = lambda: test_admin
    yield test_admin


@pytest.fixture
def sample_notifications():
    """Return a list of sample notification dicts with various severities, types, and timestamps."""
    now = datetime.now()
    return [
        {
            "id": "notif_1",
            "recipient_id": "test_user_id",
            "title": "Lead Created",
            "description": "A new lead has been created.",
            "severity": "info",
            "notification_type": "lead",
            "action_url": "/leads/123",
            "metadata": {},
            "created_at": now.isoformat(),
            "read_at": None,
            "expires_at": (now + timedelta(days=7)).isoformat()
        },
        {
            "id": "notif_2",
            "recipient_id": "test_user_id",
            "title": "Agent Error",
            "description": "An agent encountered an error.",
            "severity": "error",
            "notification_type": "agent",
            "action_url": None,
            "metadata": {"error_code": "500"},
            "created_at": (now - timedelta(seconds=30)).isoformat(),
            "read_at": None,
            "expires_at": (now + timedelta(days=7)).isoformat()
        },
        {
            "id": "notif_3",
            "recipient_id": "test_user_id",
            "title": "System Update",
            "description": "System has been updated.",
            "severity": "warning",
            "notification_type": "system",
            "action_url": "/settings",
            "metadata": {},
            "created_at": (now - timedelta(hours=1)).isoformat(),
            "read_at": now.isoformat(),
            "expires_at": (now + timedelta(days=7)).isoformat()
        }
    ]


def create_mock_notification(**overrides):
    """Helper function that generates notification dict with default values and accepts overrides."""
    defaults = {
        "id": "mock_notif_id",
        "recipient_id": "test_user_id",
        "title": "Mock Notification",
        "description": "This is a mock notification.",
        "severity": "info",
        "notification_type": "system",
        "action_url": None,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
        "read_at": None,
        "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
    }
    defaults.update(overrides)
    return defaults


def mock_supabase_query_result(data=None, count=None):
    """Helper function that creates properly formatted Supabase response objects."""
    if data is None:
        data = []
    result = MagicMock()
    result.data = data
    if count is not None:
        result.count = count
    return result


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """Autouse fixture to clear dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()