import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from backend.app.main import app


@pytest.fixture
def payload():
    start = datetime(2025, 2, 1, 10, 0, 0)
    end = start + timedelta(minutes=60)
    return {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+44 1234",
        "company": "Analytical Engines",
        "start_time": start.isoformat() + 'Z',
        "end_time": end.isoformat() + 'Z',
        "appointment_type": "strategy_session",
        "notes": "Goals: Grow",
        "timezone": "Europe/London",
    }


def test_book_success_with_auth(test_client, mock_supabase, mock_redis, payload):
    """Test successful booking with authentication"""
    # Mock external calendar and email to succeed
    with patch('backend.app.utils.external_tools.create_calendar_event', return_value={"success": True, "data": {"event_id": "evt_1"}}), \
         patch('backend.app.utils.external_tools.send_email', return_value=True):
        # Ensure no conflicts
        mock_table = mock_supabase.table.return_value
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.offset.return_value = mock_table
        mock_table.execute.return_value = type('R', (), {"data": []})()
        mock_table.insert.return_value = mock_table
        mock_table.single.return_value = mock_table

        res = test_client.post('/api/appointments/book', json=payload, headers={"Authorization": "Bearer test-token-123"})
        assert res.status_code == 200, res.text
        body = res.json()
        assert body.get('success') is True
        assert 'appointment_id' in body


def test_get_appointment_success(test_client, mock_supabase):
    """Test getting appointment details"""
    mock_appointment = {
        "id": "apt_123",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "start_time": "2025-02-01T10:00:00Z",
        "end_time": "2025-02-01T11:00:00Z",
        "appointment_type": "strategy_session",
        "status": "scheduled",
        "created_by": "test-user-id"
    }
    
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": mock_appointment})()
    
    res = test_client.get('/api/appointments/apt_123', headers={"Authorization": "Bearer test-token-123"})
    assert res.status_code == 200
    body = res.json()
    assert body.get('success') is True
    assert body.get('appointment')['id'] == 'apt_123'


def test_list_appointments_filtered_by_user(test_client, mock_supabase):
    """Test listing appointments filtered by user"""
    mock_appointments = [
        {
            "id": "apt_1",
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "start_time": "2025-02-01T10:00:00Z",
            "end_time": "2025-02-01T11:00:00Z",
            "appointment_type": "strategy_session",
            "status": "scheduled",
            "created_by": "test-user-id"
        }
    ]
    
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.offset.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": mock_appointments, "count": 1})()
    
    res = test_client.get('/api/appointments', headers={"Authorization": "Bearer test-token-123"})
    assert res.status_code == 200
    body = res.json()
    assert body.get('success') is True
    assert len(body.get('appointments', [])) == 1


def test_complete_appointment_success(test_client, mock_supabase):
    """Test completing an appointment"""
    mock_appointment = {
        "id": "apt_123",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "start_time": "2025-02-01T10:00:00Z",
        "end_time": "2025-02-01T11:00:00Z",
        "appointment_type": "strategy_session",
        "status": "scheduled"
    }
    
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": mock_appointment})()
    mock_table.update.return_value = mock_table
    
    res = test_client.patch('/api/appointments/apt_123/complete', 
                           headers={"X-API-Key": "test-key", "Authorization": "Bearer test-token-123"})
    assert res.status_code == 200
    body = res.json()
    assert body.get('success') is True
    assert body.get('message') == "Appointment marked as completed"


def test_appointment_auth_failure(test_client, mock_supabase):
    """Test authorization failure for appointment access"""
    mock_appointment = {
        "id": "apt_123",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "start_time": "2025-02-01T10:00:00Z",
        "end_time": "2025-02-01T11:00:00Z",
        "appointment_type": "strategy_session",
        "status": "scheduled",
        "created_by": "different-user-id"  # Different user
    }
    
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": mock_appointment})()
    
    res = test_client.get('/api/appointments/apt_123', headers={"Authorization": "Bearer test-token-123"})
    assert res.status_code == 403  # Forbidden