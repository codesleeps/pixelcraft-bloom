import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from backend.app.utils.notification_service import (
    create_notification,
    create_notification_for_admins,
    mark_notifications_read,
    get_unread_count
)


@pytest.mark.asyncio
async def test_create_notification_success(mock_supabase, mock_redis):
    """Test creates notification in Supabase with correct data structure and publishes event."""
    # Setup mock Supabase response
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test_notif_id"}])
    
    # Call function
    result = await create_notification(
        recipient_id="user123",
        notification_type="lead",
        severity="info",
        title="Test Title",
        message="Test Message",
        action_url="/test",
        metadata={"key": "value"},
        expires_at=datetime.now() + timedelta(days=1)
    )
    
    # Assertions
    assert result == "test_notif_id"
    
    # Verify Supabase call
    mock_supabase.table.assert_called_with("notifications")
    insert_call = mock_supabase.table.return_value.insert
    insert_call.assert_called_once()
    data = insert_call.call_args[0][0]
    assert data["recipient_id"] == "user123"
    assert data["notification_type"] == "lead"
    assert data["severity"] == "info"
    assert data["title"] == "Test Title"
    assert data["message"] == "Test Message"
    assert data["action_url"] == "/test"
    assert data["metadata"] == {"key": "value"}
    assert "expires_at" in data
    
    # Verify Redis publish
    assert len(mock_redis) == 1
    event = mock_redis[0]
    assert event["channel"] == "notifications:user:user123"
    assert event["event_type"] == "notification_created"
    assert event["data"]["notification_id"] == "test_notif_id"


@pytest.mark.asyncio
async def test_create_notification_optional_params(mock_supabase, mock_redis):
    """Test handles optional parameters correctly."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test_notif_id"}])
    
    result = await create_notification(
        recipient_id="user123",
        notification_type="lead",
        severity="info",
        title="Test Title",
        message="Test Message"
    )
    
    assert result == "test_notif_id"
    data = mock_supabase.table.return_value.insert.call_args[0][0]
    assert data["action_url"] is None
    assert data["metadata"] == {}
    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_create_notification_database_error(mock_supabase, mock_redis, caplog):
    """Test returns None on database error and logs warning."""
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
    
    result = await create_notification(
        recipient_id="user123",
        notification_type="lead",
        severity="info",
        title="Test Title",
        message="Test Message"
    )
    
    assert result is None
    assert "Failed to create notification" in caplog.text
    assert len(mock_redis) == 0  # No publish on error


@pytest.mark.asyncio
async def test_create_notification_for_admins_success(mock_supabase, mock_redis):
    """Test queries admins and creates notifications for each."""
    # Mock admin query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
        {"user_id": "admin1"},
        {"user_id": "admin2"}
    ])
    
    with patch('backend.app.utils.notification_service.create_notification') as mock_create:
        mock_create.return_value = "notif_id"
        
        await create_notification_for_admins(
            notification_type="system",
            severity="warning",
            title="Admin Alert",
            message="Test Message"
        )
        
        # Verify admin query
        mock_supabase.table.assert_called_with("user_profiles")
        mock_supabase.table.return_value.select.assert_called_with("user_id")
        mock_supabase.table.return_value.select.return_value.eq.assert_called_with("role", "admin")
        
        # Verify create_notification calls
        assert mock_create.call_count == 2
        calls = mock_create.call_args_list
        assert calls[0][0][0] == "admin1"  # recipient_id
        assert calls[1][0][0] == "admin2"


@pytest.mark.asyncio
async def test_create_notification_for_admins_empty_list(mock_supabase):
    """Test handles empty admin list gracefully."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    
    with patch('backend.app.utils.notification_service.create_notification') as mock_create:
        await create_notification_for_admins(
            notification_type="system",
            severity="warning",
            title="Admin Alert",
            message="Test Message"
        )
        
        mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_create_notification_for_admins_database_error(mock_supabase, caplog):
    """Test handles database errors gracefully and logs warning."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
    
    await create_notification_for_admins(
        notification_type="system",
        severity="warning",
        title="Admin Alert",
        message="Test Message"
    )
    
    assert "Failed to create notifications for admins" in caplog.text


@pytest.mark.asyncio
async def test_mark_notifications_read_success(mock_supabase):
    """Test updates read_at for specified notifications."""
    mock_supabase.table.return_value.update.return_value.in_.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}, {}])  # 2 updated
    
    result = await mark_notifications_read(["id1", "id2"], "user123")
    
    assert result == 2
    
    # Verify Supabase calls
    mock_supabase.table.assert_called_with("notifications")
    update_chain = mock_supabase.table.return_value.update
    update_chain.assert_called_with({"read_at": "now()"})
    update_chain.return_value.in_.assert_called_with("id", ["id1", "id2"])
    update_chain.return_value.in_.return_value.eq.assert_called_with("recipient_id", "user123")


@pytest.mark.asyncio
async def test_mark_notifications_read_empty_list(mock_supabase):
    """Test handles empty ID list."""
    result = await mark_notifications_read([], "user123")
    
    assert result == 0
    mock_supabase.table.return_value.update.assert_not_called()


@pytest.mark.asyncio
async def test_mark_notifications_read_database_error(mock_supabase, caplog):
    """Test returns 0 on database error and logs warning."""
    mock_supabase.table.return_value.update.return_value.in_.return_value.eq.return_value.execute.side_effect = Exception("DB Error")
    
    result = await mark_notifications_read(["id1"], "user123")
    
    assert result == 0
    assert "Failed to mark notifications read" in caplog.text


@pytest.mark.asyncio
async def test_get_unread_count_success(mock_supabase):
    """Test counts unread notifications for user."""
    mock_result = MagicMock()
    mock_result.count = 5
    mock_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
    
    result = await get_unread_count("user123")
    
    assert result == 5
    
    # Verify Supabase calls
    mock_supabase.table.assert_called_with("notifications")
    select_chain = mock_supabase.table.return_value.select
    select_chain.assert_called_with("id", count="exact")
    select_chain.return_value.eq.assert_called_with("recipient_id", "user123")
    select_chain.return_value.eq.return_value.is_.assert_called_with("read_at", None)


@pytest.mark.asyncio
async def test_get_unread_count_no_unread(mock_supabase):
    """Test returns 0 when no unread notifications."""
    mock_result = MagicMock()
    mock_result.count = 0
    mock_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
    
    result = await get_unread_count("user123")
    
    assert result == 0


@pytest.mark.asyncio
async def test_get_unread_count_database_error(mock_supabase, caplog):
    """Test returns 0 on database error and logs warning."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.side_effect = Exception("DB Error")
    
    result = await get_unread_count("user123")
    
    assert result == 0
    assert "Failed to get unread count" in caplog.text


@pytest.mark.asyncio
async def test_redis_integration_publish_on_create(mock_supabase, mock_redis):
    """Test notification creation publishes to correct Redis channel with full data."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "notif123"}])
    
    await create_notification(
        recipient_id="user456",
        notification_type="agent",
        severity="error",
        title="Error Alert",
        message="Something went wrong",
        metadata={"error": "details"}
    )
    
    assert len(mock_redis) == 1
    event = mock_redis[0]
    assert event["channel"] == "notifications:user:user456"
    assert event["event_type"] == "notification_created"
    data = event["data"]
    assert data["notification_id"] == "notif123"
    assert data["recipient_id"] == "user456"
    assert data["notification_type"] == "agent"
    assert data["severity"] == "error"
    assert data["title"] == "Error Alert"
    assert data["message"] == "Something went wrong"
    assert data["metadata"] == {"error": "details"}


@pytest.mark.asyncio
async def test_redis_unavailable_does_not_prevent_creation(mock_supabase):
    """Test Redis unavailable doesn't prevent notification creation."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "notif123"}])
    
    # Mock publish_analytics_event to do nothing (Redis unavailable)
    with patch('backend.app.utils.notification_service.publish_analytics_event'):
        result = await create_notification(
            recipient_id="user123",
            notification_type="lead",
            severity="info",
            title="Test",
            message="Test"
        )
        
        assert result == "notif123"


@pytest.mark.asyncio
async def test_data_validation_required_params(mock_supabase, mock_redis):
    """Test required parameters are validated and data structure matches schema."""
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "notif123"}])
    
    await create_notification(
        recipient_id="user123",
        notification_type="lead",
        severity="info",
        title="Test Title",
        message="Test Message"
    )
    
    data = mock_supabase.table.return_value.insert.call_args[0][0]
    required_fields = ["recipient_id", "notification_type", "severity", "title", "message", "metadata", "expires_at"]
    for field in required_fields:
        assert field in data
    assert isinstance(data["metadata"], dict)
    assert data["metadata"] == {}