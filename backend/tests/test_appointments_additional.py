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


def test_book_validation_errors(test_client, mock_supabase, payload):
    """Test various validation error cases"""
    # Test invalid email
    bad_payload = dict(payload)
    bad_payload['email'] = 'invalid-email'
    res = test_client.post('/api/appointments/book', json=bad_payload)
    assert res.status_code == 422

    # Test missing required fields
    bad_payload = dict(payload)
    del bad_payload['name']
    res = test_client.post('/api/appointments/book', json=bad_payload)
    assert res.status_code == 422

    # Test invalid time order
    bad_payload = dict(payload)
    bad_payload['start_time'] = payload['end_time']
    bad_payload['end_time'] = payload['start_time']
    res = test_client.post('/api/appointments/book', json=bad_payload)
    assert res.status_code == 422

    # Test invalid appointment type
    bad_payload = dict(payload)
    bad_payload['appointment_type'] = 'invalid_type'
    res = test_client.post('/api/appointments/book', json=bad_payload)
    assert res.status_code == 422


def test_book_external_service_failure(test_client, mock_supabase, mock_redis, payload):
    """Test handling of external service failures"""
    # Mock calendar event creation to fail
    with patch('backend.app.utils.external_tools.create_calendar_event', return_value={"success": False, "error": "Calendar unavailable"}), \
         patch('backend.app.utils.external_tools.send_email', return_value=True):
        # Ensure no conflicts
        mock_table = mock_supabase.table.return_value
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.offset.return_value = mock_table
        mock_table.execute.return_value = type('R', (), {"data": []})()
        
        # Should still succeed even if calendar fails (fallback behavior)
        res = test_client.post('/api/appointments/book', json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body.get('success') is True
        assert 'appointment_id' in body


def test_book_database_insert_failure(test_client, mock_supabase, mock_redis, payload):
    """Test handling of database insert failures"""
    with patch('backend.app.utils.external_tools.create_calendar_event', return_value={"success": True, "data": {"event_id": "evt_1"}}), \
         patch('backend.app.utils.external_tools.send_email', return_value=True):
        # Mock database insert to fail
        mock_table = mock_supabase.table.return_value
        mock_table.insert.side_effect = Exception("Database error")
        
        res = test_client.post('/api/appointments/book', json=payload)
        assert res.status_code == 500
        body = res.json()
        assert "Failed to book appointment" in body.get('detail', '')


def test_get_availability_invalid_date(test_client):
    """Test get_availability with invalid date parameter"""
    res = test_client.get('/api/appointments/availability?date=invalid-date&duration=60&timezone=UTC')
    assert res.status_code == 422


def test_get_availability_missing_params(test_client):
    """Test get_availability with missing required parameters"""
    res = test_client.get('/api/appointments/availability')
    assert res.status_code == 422


def test_get_appointment_not_found(test_client, mock_supabase):
    """Test get_appointment with non-existent appointment ID"""
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": None})()
    
    res = test_client.get('/api/appointments/non-existent-id')
    assert res.status_code == 404


def test_list_appointments_with_filters(test_client, mock_supabase):
    """Test list_appointments with various filter combinations"""
    mock_data = [
        {"id": "apt_1", "status": "scheduled", "email": "user1@example.com"},
        {"id": "apt_2", "status": "cancelled", "email": "user2@example.com"},
    ]
    
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.offset.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": mock_data, "count": len(mock_data)})()
    
    # Test with status filter
    res = test_client.get('/api/appointments?status=scheduled')
    assert res.status_code == 200
    body = res.json()
    assert body.get('success') is True
    
    # Test with email filter
    res = test_client.get('/api/appointments?email=user1@example.com')
    assert res.status_code == 200
    body = res.json()
    assert body.get('success') is True


def test_reschedule_appointment_not_found(test_client, mock_supabase):
    """Test reschedule_appointment with non-existent appointment"""
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": None})()
    
    payload = {
        "new_start_time": "2025-02-01T11:00:00Z",
        "new_end_time": "2025-02-01T12:00:00Z"
    }
    
    res = test_client.patch('/api/appointments/non-existent-id/reschedule', json=payload, headers={"X-API-Key": "test-key"})
    assert res.status_code == 404


def test_cancel_appointment_not_found(test_client, mock_supabase):
    """Test cancel_appointment with non-existent appointment"""
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": None})()
    
    payload = {"reason": "Changed my mind"}
    
    res = test_client.patch('/api/appointments/non-existent-id/cancel', json=payload, headers={"X-API-Key": "test-key"})
    assert res.status_code == 404