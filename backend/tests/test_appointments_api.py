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


def test_book_success(test_client, mock_supabase, mock_redis, payload):
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

        res = test_client.post('/api/appointments/book', json=payload)
        assert res.status_code == 200, res.text
        body = res.json()
        assert body.get('success') is True
        assert 'appointment_id' in body


def test_book_validation_error(test_client, mock_supabase, payload):
    bad = dict(payload)
    bad['appointment_type'] = 'unknown'
    res = test_client.post('/api/appointments/book', json=bad)
    # Pydantic validation or manual validation should reject
    assert res.status_code in (400, 422)


def test_book_conflict(test_client, mock_supabase, mock_redis, payload):
    # Simulate an existing scheduled appointment overlapping the same window
    existing = dict(payload)
    existing.update({"id": "apt_existing", "status": "scheduled"})

    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.offset.return_value = mock_table
    mock_table.execute.return_value = type('R', (), {"data": [existing]})()

    res = test_client.post('/api/appointments/book', json=payload)
    assert res.status_code in (400, 409)
