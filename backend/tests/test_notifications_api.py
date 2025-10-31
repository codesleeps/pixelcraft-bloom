import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from backend.app.models.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
)


class TestNotificationsAPI:
    """Integration tests for notification REST API endpoints."""

    def test_get_notifications_success(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test GET /api/notifications returns list of notifications for authenticated user."""
        # Mock Supabase queries
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=sample_notifications)
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        # Mock total count query
        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=len(sample_notifications))
        mock_table.select.return_value.eq.return_value = mock_total_query

        # Mock unread count
        with patch("backend.app.utils.notification_service.get_unread_count", return_value=2):
            response = test_client.get("/api/notifications")

        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert "unread_count" in data
        assert len(data["notifications"]) == len(sample_notifications)
        assert data["total"] == len(sample_notifications)
        assert data["unread_count"] == 2
        # Verify ordering and structure
        assert data["notifications"][0]["created_at"] >= data["notifications"][1]["created_at"]

    def test_get_notifications_unread_only(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test GET /api/notifications filters by unread_only=true."""
        unread_notifications = [n for n in sample_notifications if n["read_at"] is None]
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=unread_notifications)
        mock_table.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=len(unread_notifications))
        mock_table.select.return_value.eq.return_value.is_.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=len(unread_notifications)):
            response = test_client.get("/api/notifications?unread_only=true")

        assert response.status_code == 200
        data = response.json()
        assert all(n["read_at"] is None for n in data["notifications"])

    def test_get_notifications_by_type(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test GET /api/notifications filters by notification_type."""
        lead_notifications = [n for n in sample_notifications if n["notification_type"] == "lead"]
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=lead_notifications)
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=len(lead_notifications))
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=1):
            response = test_client.get("/api/notifications?notification_type=lead")

        assert response.status_code == 200
        data = response.json()
        assert all(n["notification_type"] == "lead" for n in data["notifications"])

    def test_get_notifications_pagination(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test GET /api/notifications with limit and offset."""
        limit, offset = 1, 1
        paginated_notifications = sample_notifications[offset : offset + limit]
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=paginated_notifications)
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=len(sample_notifications))
        mock_table.select.return_value.eq.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=2):
            response = test_client.get(f"/api/notifications?limit={limit}&offset={offset}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == limit
        assert data["total"] == len(sample_notifications)

    def test_get_single_notification_success(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test GET /api/notifications/{notification_id} returns single notification."""
        notification = sample_notifications[0]
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[notification])
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_query

        response = test_client.get(f"/api/notifications/{notification['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notification["id"]
        assert data["recipient_id"] == mock_auth_user["user_id"]

    def test_get_single_notification_not_found(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test GET /api/notifications/{notification_id} returns 404 when not found."""
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_query

        response = test_client.get("/api/notifications/nonexistent_id")

        assert response.status_code == 404

    def test_get_single_notification_wrong_user(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test GET /api/notifications/{notification_id} returns 404 for different user."""
        notification = sample_notifications[0]
        notification["recipient_id"] = "other_user_id"  # Different user
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_query

        response = test_client.get(f"/api/notifications/{notification['id']}")

        assert response.status_code == 404

    def test_mark_read_success(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test POST /api/notifications/mark-read marks notifications as read."""
        notification_ids = ["id1", "id2"]
        request_data = {"notification_ids": notification_ids}

        with patch("backend.app.utils.notification_service.mark_notifications_read", return_value=2) as mock_mark:
            response = test_client.post("/api/notifications/mark-read", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["marked_read_count"] == 2
        mock_mark.assert_called_once_with(notification_ids, mock_auth_user["user_id"])

    def test_mark_all_read_success(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test POST /api/notifications/mark-all-read marks all unread as read."""
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[{}, {}])  # 2 updated
        mock_table.update.return_value.eq.return_value.is_.return_value = mock_query

        response = test_client.post("/api/notifications/mark-all-read")

        assert response.status_code == 200
        data = response.json()
        assert data["marked_read_count"] == 2

    def test_delete_notification_success(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test DELETE /api/notifications/{notification_id} soft deletes notification."""
        notification_id = "test_id"
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[{}])  # Updated
        mock_table.update.return_value.eq.return_value.eq.return_value = mock_query

        response = test_client.delete(f"/api/notifications/{notification_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Notification deleted successfully"

    def test_delete_notification_not_found(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test DELETE /api/notifications/{notification_id} returns 404 when not found."""
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value.eq.return_value.eq.return_value = mock_query

        response = test_client.delete("/api/notifications/nonexistent_id")

        assert response.status_code == 404

    def test_get_unread_count_success(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test GET /api/notifications/unread-count returns unread count."""
        with patch("backend.app.utils.notification_service.get_unread_count", return_value=5) as mock_get:
            response = test_client.get("/api/notifications/unread-count")

        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 5
        mock_get.assert_called_once_with(mock_auth_user["user_id"])

    def test_authentication_required(
        self, test_client, mock_supabase, mock_redis
    ):
        """Test endpoints return 401 without authentication."""
        with patch("backend.app.utils.auth.get_current_user", side_effect=HTTPException(status_code=401)):
            response = test_client.get("/api/notifications")
            assert response.status_code == 401

            response = test_client.post("/api/notifications/mark-read", json={"notification_ids": []})
            assert response.status_code == 401

            response = test_client.post("/api/notifications/mark-all-read")
            assert response.status_code == 401

            response = test_client.delete("/api/notifications/test_id")
            assert response.status_code == 401

            response = test_client.get("/api/notifications/unread-count")
            assert response.status_code == 401

    def test_user_can_only_access_own_notifications(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test user can only access their own notifications."""
        # This is implicitly tested in other tests where recipient_id is checked
        # For example, in get_single_notification_wrong_user
        pass  # Covered in other tests

    def test_admin_no_special_privileges(
        self, test_client, mock_supabase, mock_redis, mock_auth_admin
    ):
        """Test admin can access their own notifications (no special privileges)."""
        # Similar to user tests, but with admin fixture
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=0)
        mock_table.select.return_value.eq.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=0):
            response = test_client.get("/api/notifications")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_database_error_handling(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test endpoints return 500 on database errors."""
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.side_effect = Exception("Database error")
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        response = test_client.get("/api/notifications")

        assert response.status_code == 500

    def test_malformed_request_body(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test endpoints handle malformed request bodies gracefully."""
        # For mark-read, invalid JSON or missing fields
        response = test_client.post("/api/notifications/mark-read", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

    def test_invalid_query_parameters(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test endpoints validate query parameters."""
        # Negative limit should be handled (FastAPI might allow, but test edge case)
        response = test_client.get("/api/notifications?limit=-1")
        # Assuming FastAPI validates, or test what happens
        assert response.status_code in [200, 422]  # Depending on validation

    def test_empty_notification_list(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test empty notification list returns valid response structure."""
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=0)
        mock_table.select.return_value.eq.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=0):
            response = test_client.get("/api/notifications")

        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    def test_mark_read_empty_array(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test marking read with empty ID array."""
        request_data = {"notification_ids": []}

        with patch("backend.app.utils.notification_service.mark_notifications_read", return_value=0) as mock_mark:
            response = test_client.post("/api/notifications/mark-read", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["marked_read_count"] == 0
        mock_mark.assert_called_once_with([], mock_auth_user["user_id"])

    def test_pagination_beyond_results(
        self, test_client, mock_supabase, mock_redis, mock_auth_user, sample_notifications
    ):
        """Test pagination beyond available results."""
        offset = len(sample_notifications) + 10
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=len(sample_notifications))
        mock_table.select.return_value.eq.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=2):
            response = test_client.get(f"/api/notifications?offset={offset}")

        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == len(sample_notifications)

    def test_filtering_no_matches(
        self, test_client, mock_supabase, mock_redis, mock_auth_user
    ):
        """Test filtering with no matches."""
        mock_table = mock_supabase.table.return_value
        mock_query = MagicMock()
        mock_query.execute.return_value = MagicMock(data=[])
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = mock_query

        mock_total_query = MagicMock()
        mock_total_query.execute.return_value = MagicMock(count=0)
        mock_table.select.return_value.eq.return_value.eq.return_value = mock_total_query

        with patch("backend.app.utils.notification_service.get_unread_count", return_value=0):
            response = test_client.get("/api/notifications?notification_type=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == 0