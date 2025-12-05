import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set OLLAMA_HOST to avoid startup errors if config is loaded
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
        
        yield client_mock

def test_book_appointment_success(mock_supabase):
    """Test booking an appointment with mock services"""
    # Ensure no calendar credentials so it uses mock
    with patch.dict("os.environ", {"OLLAMA_HOST": "http://localhost:11434"}, clear=True):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "start_time": "2025-12-25T10:00:00Z",
            "end_time": "2025-12-25T11:00:00Z",
            "appointment_type": "strategy_session",
            "notes": "Test appointment"
        }
        
        response = client.post("/api/appointments/book", json=payload)
        
        # Debug output if failed
        if response.status_code != 200:
            print(f"Response: {response.text}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "appointment_id" in data
        assert data["message"] == "Appointment booked successfully"
        
        # Verify Supabase insert was called
        # Note: The exact call arguments would be complex to match, but we can check call count
        assert mock_supabase.table.call_count >= 1

def test_get_availability_mock():
    """Test availability endpoint falls back to mock slots"""
    # Ensure no calendar credentials
    with patch.dict("os.environ", {"OLLAMA_HOST": "http://localhost:11434"}, clear=True):
        response = client.get("/api/appointments/availability?date=2025-12-25")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["slots"]) > 0
        assert data["slots"][0]["available"] is True

@pytest.mark.asyncio
async def test_crm_integration_mock():
    """Test CRM integration falls back to mock"""
    from app.utils.external_tools import create_crm_contact
    
    # Ensure no CRM credentials
    with patch.dict("os.environ", {}, clear=True):
        result = await create_crm_contact(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            company="Acme Corp"
        )
        
        assert result["success"] is True
        assert result["data"]["mock"] is True
        assert result["data"]["status"] == "mock_created"

@pytest.mark.asyncio
async def test_email_service_mock():
    """Test email service falls back to mock"""
    from app.utils.external_tools import send_email
    
    # Ensure no email credentials
    with patch.dict("os.environ", {}, clear=True):
        result = await send_email(
            to_email="test@example.com",
            subject="Test Email",
            html_content="<p>Hello</p>"
        )
        
        assert result["success"] is True
        assert result["data"]["mock"] is True
        assert result["data"]["status"] == "mock_sent"
