import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.utils.supabase_client import DummySupabaseClient

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.routes.appointments.get_supabase_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_external_tools():
    with patch("app.routes.appointments.check_calendar_availability") as mock_check, \
         patch("app.routes.appointments.create_calendar_event") as mock_create, \
         patch("app.routes.appointments.send_email") as mock_email:
        
        mock_check.return_value = {
            "success": True, 
            "data": {
                "available_slots": [
                    {"start": "2025-12-02T10:00:00Z", "end": "2025-12-02T11:00:00Z"},
                    {"start": "2025-12-02T14:00:00Z", "end": "2025-12-02T15:00:00Z"}
                ]
            }
        }
        mock_create.return_value = {"success": True, "data": {"event_id": "evt_123"}}
        mock_email.return_value = {"success": True}
        
        yield {
            "check": mock_check,
            "create": mock_create,
            "email": mock_email
        }

def test_get_availability(mock_external_tools):
    response = client.get("/api/appointments/availability?date=2025-12-02&timezone=UTC")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["slots"]) > 0
    assert data["slots"][0]["start_time"] == "2025-12-02T10:00:00+00:00"

def test_book_appointment(mock_supabase, mock_external_tools):
    # Mock Supabase insert
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "appt_123"}])
    # Mock Supabase select (conflict check)
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])

    payload = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "company": "Acme Inc",
        "start_time": "2025-12-02T10:00:00Z",
        "end_time": "2025-12-02T11:00:00Z",
        "appointment_type": "strategy_session",
        "notes": "Looking for growth",
        "timezone": "UTC"
    }
    
    response = client.post("/api/appointments/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "appointment_id" in data
    
    # Verify external calls
    mock_external_tools["create"].assert_called_once()
    mock_external_tools["email"].assert_called_once()

def test_book_appointment_conflict(mock_supabase, mock_external_tools):
    # Mock Supabase conflict
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
        data=[{
            "start_time": "2025-12-02T10:00:00Z",
            "end_time": "2025-12-02T11:00:00Z",
            "status": "scheduled"
        }]
    )

    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "0987654321",
        "start_time": "2025-12-02T10:00:00Z",
        "end_time": "2025-12-02T11:00:00Z",
        "appointment_type": "discovery_call",
        "timezone": "UTC"
    }
    
    response = client.post("/api/appointments/book", json=payload)
    assert response.status_code == 409
    assert "conflict" in response.json()["detail"].lower()
