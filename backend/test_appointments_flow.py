import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import json

# Set OLLAMA_HOST to avoid startup errors
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from app.main import app
from app.utils.auth import get_current_user

# Mock user
mock_user = {
    "user_id": "test-user-id",
    "email": "test@example.com",
    "role": "user",
    "metadata": {"name": "Test User"}
}

def mock_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.routes.appointments.get_supabase_client") as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        
        # Mock chain: table().insert().execute()
        table_mock = MagicMock()
        client_mock.table.return_value = table_mock
        
        # Mock select for conflict check
        select_mock = MagicMock()
        table_mock.select.return_value = select_mock
        in_mock = MagicMock()
        select_mock.in_.return_value = in_mock
        in_execute = MagicMock()
        in_execute.data = [] # No existing appointments
        in_mock.execute.return_value = in_execute
        
        # Mock insert
        insert_mock = MagicMock()
        table_mock.insert.return_value = insert_mock
        insert_execute = MagicMock()
        insert_mock.execute.return_value = insert_execute
        insert_execute.data = [{"id": "new-appointment-id"}]
        
        yield client_mock

def test_book_appointment_api_flow(mock_supabase):
    """Test the full appointment booking flow via API"""
    # Mock external tools to avoid real calls
    with patch("app.routes.appointments.create_calendar_event") as mock_calendar, \
         patch("app.routes.appointments.send_email") as mock_email:
        
        mock_calendar.return_value = {"success": True, "data": {"event_id": "evt_123"}}
        mock_email.return_value = {"success": True}
        
        payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-0123",
            "start_time": "2025-12-26T14:00:00Z",
            "end_time": "2025-12-26T15:00:00Z",
            "appointment_type": "strategy_session",
            "notes": "Integration test appointment"
        }
        
        response = client.post("/api/appointments/book", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "appointment_id" in data
        assert len(data["appointment_id"]) > 0
        
        # Verify calendar event was created
        mock_calendar.assert_called_once()
        # Verify email was sent
        mock_email.assert_called()

def test_get_availability_api_flow():
    """Test availability endpoint"""
    with patch("app.routes.appointments.check_calendar_availability") as mock_check:
        mock_check.return_value = {
            "success": True,
            "data": {
                "available_slots": [
                    {"start": "2025-12-26T09:00:00Z", "end": "2025-12-26T10:00:00Z"}
                ]
            }
        }
        
        response = client.get("/api/appointments/availability?date=2025-12-26")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["slots"]) == 1
        assert data["slots"][0]["start_time"] == "2025-12-26T09:00:00+00:00"
