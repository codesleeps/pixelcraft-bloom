import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("app.routes.analytics.get_supabase_client") as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock

def test_get_model_metrics(mock_supabase):
    # Override dependency
    from app.utils.auth import require_admin
    app.dependency_overrides[require_admin] = lambda: {"user_id": "admin-id", "role": "admin"}
    
    try:
        # Mock Supabase response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "model_name": "mistral:7b",
                "latency": 0.5,
                "success": True,
                "token_usage": 100,
                "timestamp": time.time(),
                "error": None
            },
            {
                "model_name": "mistral:7b",
                "latency": 0.6,
                "success": True,
                "token_usage": 150,
                "timestamp": time.time(),
                "error": None
            },
            {
                "model_name": "llama3",
                "latency": 0.0,
                "success": False,
                "token_usage": 0,
                "timestamp": time.time(),
                "error": "Timeout"
            }
        ]
        
        # Setup chain: table -> select -> gte -> lte -> execute
        mock_supabase.table.return_value \
            .select.return_value \
            .gte.return_value \
            .lte.return_value \
            .execute.return_value = mock_response

        response = client.get("/api/analytics/models/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        
        # Verify mistral:7b metrics
        mistral = next(m for m in data if m["model_name"] == "mistral:7b")
        assert mistral["total_requests"] == 2
        assert mistral["avg_latency"] == 0.55
        assert mistral["success_rate"] == 1.0
        assert mistral["total_tokens"] == 250
        assert mistral["error_count"] == 0
        
        # Verify llama3 metrics
        llama = next(m for m in data if m["model_name"] == "llama3")
        assert llama["total_requests"] == 1
        assert llama["success_rate"] == 0.0
        assert llama["error_count"] == 1
    finally:
        app.dependency_overrides = {}

def test_get_model_metrics_empty(mock_supabase):
    from app.utils.auth import require_admin
    app.dependency_overrides[require_admin] = lambda: {"user_id": "admin-id", "role": "admin"}
    
    try:
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase.table.return_value \
            .select.return_value \
            .gte.return_value \
            .lte.return_value \
            .execute.return_value = mock_response

        response = client.get("/api/analytics/models/metrics")
        
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides = {}
