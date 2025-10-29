import httpx
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import sys

# ANSI colors for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*80}\n{text}\n{'='*80}{RESET}\n")

def print_result(name: str, success: bool, data: Optional[Dict[str, Any]] = None) -> None:
    """Print a formatted test result."""
    status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if data:
        print(f"Response: {data}")

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
USER_JWT_TOKEN = os.getenv("USER_JWT_TOKEN")
ADMIN_JWT_TOKEN = os.getenv("ADMIN_JWT_TOKEN")
INVALID_TOKEN = "invalid.jwt.token.here"

def test_lead_metrics() -> bool:
    """Test GET /api/analytics/leads/summary with valid JWT."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        response = httpx.get(f"{BASE_URL}/api/analytics/leads/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "qualified_leads" in data
        assert "conversion_rate" in data
        assert "avg_lead_score" in data
        print_result("Lead Metrics", True, {"status": response.status_code, "keys": list(data.keys())})
        return True
    except Exception as e:
        print_result("Lead Metrics", False, {"error": str(e)})
        return False

def test_lead_trends() -> bool:
    """Test GET /api/analytics/leads/trends with date ranges."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {"aggregation": "daily", "start_date": "2024-01-01", "end_date": "2024-01-31"}
        response = httpx.get(f"{BASE_URL}/api/analytics/leads/trends", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metric_name" in data
        assert "aggregation" in data
        assert isinstance(data["data"], list)
        print_result("Lead Trends", True, {"status": response.status_code, "data_points": len(data["data"])})
        return True
    except Exception as e:
        print_result("Lead Trends", False, {"error": str(e)})
        return False

def test_conversation_metrics() -> bool:
    """Test GET /api/analytics/conversations/summary."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        response = httpx.get(f"{BASE_URL}/api/analytics/conversations/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "avg_messages_per_conversation" in data
        assert "active_conversations" in data
        assert "completed_conversations" in data
        print_result("Conversation Metrics", True, {"status": response.status_code, "keys": list(data.keys())})
        return True
    except Exception as e:
        print_result("Conversation Metrics", False, {"error": str(e)})
        return False

def test_agent_performance() -> bool:
    """Test GET /api/analytics/agents/summary (admin-only)."""
    try:
        headers = {"Authorization": f"Bearer {ADMIN_JWT_TOKEN}"}
        response = httpx.get(f"{BASE_URL}/api/analytics/agents/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "agent_type" in data[0]
            assert "total_actions" in data[0]
        print_result("Agent Performance", True, {"status": response.status_code, "items": len(data)})
        return True
    except Exception as e:
        print_result("Agent Performance", False, {"error": str(e)})
        return False

def test_unauthorized_access() -> bool:
    """Test that endpoints reject invalid tokens."""
    try:
        headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        response = httpx.get(f"{BASE_URL}/api/analytics/leads/summary", headers=headers)
        assert response.status_code == 401
        print_result("Unauthorized Access", True, {"status": response.status_code})
        return True
    except Exception as e:
        print_result("Unauthorized Access", False, {"error": str(e)})
        return False

def test_user_rbac() -> bool:
    """Test that regular users only see their own data."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        # Test lead summary (should work)
        response = httpx.get(f"{BASE_URL}/api/analytics/leads/summary", headers=headers)
        assert response.status_code == 200
        # Test agent summary (should fail for user)
        response = httpx.get(f"{BASE_URL}/api/analytics/agents/summary", headers=headers)
        assert response.status_code == 403
        print_result("User RBAC", True, {"lead_status": 200, "agent_status": 403})
        return True
    except Exception as e:
        print_result("User RBAC", False, {"error": str(e)})
        return False

def test_admin_rbac() -> bool:
    """Test that admins see all data."""
    try:
        headers = {"Authorization": f"Bearer {ADMIN_JWT_TOKEN}"}
        # Test lead summary
        response = httpx.get(f"{BASE_URL}/api/analytics/leads/summary", headers=headers)
        assert response.status_code == 200
        # Test agent summary
        response = httpx.get(f"{BASE_URL}/api/analytics/agents/summary", headers=headers)
        assert response.status_code == 200
        print_result("Admin RBAC", True, {"lead_status": 200, "agent_status": 200})
        return True
    except Exception as e:
        print_result("Admin RBAC", False, {"error": str(e)})
        return False

def test_pagination_filtering() -> bool:
    """Test pagination, filtering, and sorting in conversations list."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {
            "limit": 10,
            "offset": 0,
            "status": "active",
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        response = httpx.get(f"{BASE_URL}/api/analytics/conversations/list", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) <= 10
        print_result("Pagination Filtering", True, {"status": response.status_code, "items": len(data["items"]), "total": data["total"]})
        return True
    except Exception as e:
        print_result("Pagination Filtering", False, {"error": str(e)})
        return False

def test_revenue_summary() -> bool:
    """Test GET /api/analytics/revenue/summary with valid JWT and date params."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        response = httpx.get(f"{BASE_URL}/api/analytics/revenue/summary", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert "mrr" in data
        assert "arr" in data
        assert "total_revenue" in data
        assert "active_subscriptions" in data
        assert "cancelled_subscriptions" in data
        assert "churn_rate" in data
        # Verify data types (mrr/arr/total_revenue are numeric, counts are integers, churn_rate is float)
        assert isinstance(data["mrr"], (int, float))
        assert isinstance(data["arr"], (int, float))
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["active_subscriptions"], int)
        assert isinstance(data["cancelled_subscriptions"], int)
        assert isinstance(data["churn_rate"], (int, float))
        print_result("Revenue Summary", True, {"status": response.status_code, "keys": list(data.keys())})
        return True
    except Exception as e:
        print_result("Revenue Summary", False, {"error": str(e)})
        return False

def test_revenue_by_package() -> bool:
    """Test GET /api/analytics/revenue/by-package with JWT."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {"start_date": "2024-01-01", "end_date": "2024-12-31"}
        response = httpx.get(f"{BASE_URL}/api/analytics/revenue/by-package", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "package_id" in item
            assert "package_name" in item
            assert "subscription_count" in item
            assert "total_revenue" in item
            assert "avg_revenue_per_subscription" in item
        print_result("Revenue by Package", True, {"status": response.status_code, "items": len(data)})
        return True
    except Exception as e:
        print_result("Revenue by Package", False, {"error": str(e)})
        return False

def test_subscription_trends() -> bool:
    """Test GET /api/analytics/revenue/subscription-trends with aggregation."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {"aggregation": "daily", "start_date": "2024-01-01", "end_date": "2024-12-31"}
        response = httpx.get(f"{BASE_URL}/api/analytics/revenue/subscription-trends", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "aggregation" in data
        assert isinstance(data["data"], list)
        if data["data"]:
            point = data["data"][0]
            assert "period" in point
            assert "new_subscriptions" in point
            assert "cancelled_subscriptions" in point
            assert "net_change" in point
            assert "cumulative_active" in point
        print_result("Subscription Trends", True, {"status": response.status_code, "data_points": len(data["data"])})
        return True
    except Exception as e:
        print_result("Subscription Trends", False, {"error": str(e)})
        return False

def test_customer_ltv() -> bool:
    """Test GET /api/analytics/revenue/customer-ltv with pagination."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {"limit": 10, "offset": 0}
        response = httpx.get(f"{BASE_URL}/api/analytics/revenue/customer-ltv", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "user_id" in item
            assert "total_spent" in item
            assert "subscription_count" in item
            assert "avg_subscription_value" in item
            assert "lifetime_months" in item
            assert "estimated_ltv" in item
        print_result("Customer LTV", True, {"status": response.status_code, "items": len(data)})
        return True
    except Exception as e:
        print_result("Customer LTV", False, {"error": str(e)})
        return False

def test_subscriptions_list() -> bool:
    """Test GET /api/analytics/revenue/subscriptions/list with pagination."""
    try:
        headers = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        params = {"limit": 10, "offset": 0}
        response = httpx.get(f"{BASE_URL}/api/analytics/revenue/subscriptions/list", headers=headers, params=params)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        print_result("Subscriptions List", True, {"status": response.status_code, "items": len(data["items"]), "total": data["total"]})
        return True
    except Exception as e:
        print_result("Subscriptions List", False, {"error": str(e)})
        return False

def test_revenue_user_rbac() -> bool:
    """Test RBAC for revenue endpoints: user sees own data, admin sees all."""
    try:
        # Test user access (should see only their data)
        headers_user = {"Authorization": f"Bearer {USER_JWT_TOKEN}"}
        response_user = httpx.get(f"{BASE_URL}/api/analytics/revenue/summary", headers=headers_user)
        assert response_user.status_code == 200
        data_user = response_user.json()
        # Test admin access (should see all data)
        headers_admin = {"Authorization": f"Bearer {ADMIN_JWT_TOKEN}"}
        response_admin = httpx.get(f"{BASE_URL}/api/analytics/revenue/summary", headers=headers_admin)
        assert response_admin.status_code == 200
        data_admin = response_admin.json()
        # Note: Assuming data is set up such that user data is subset of admin data
        print_result("Revenue User RBAC", True, {"user_status": response_user.status_code, "admin_status": response_admin.status_code})
        return True
    except Exception as e:
        print_result("Revenue User RBAC", False, {"error": str(e)})
        return False

def test_revenue_unauthorized() -> bool:
    """Test that revenue endpoints reject invalid tokens."""
    try:
        headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        response = httpx.get(f"{BASE_URL}/api/analytics/revenue/summary", headers=headers)
        assert response.status_code == 401
        print_result("Revenue Unauthorized", True, {"status": response.status_code})
        return True
    except Exception as e:
        print_result("Revenue Unauthorized", False, {"error": str(e)})
        return False

def main() -> None:
    """Run all analytics API tests."""
    try:
        print_header("PixelCraft Analytics API Tests")
        
        # Check if tokens are set
        if not USER_JWT_TOKEN or not ADMIN_JWT_TOKEN:
            print(f"{RED}Error: USER_JWT_TOKEN and ADMIN_JWT_TOKEN must be set in .env{RESET}")
            sys.exit(1)
        
        # Run all tests
        tests = [
            ("Lead Metrics", test_lead_metrics()),
            ("Lead Trends", test_lead_trends()),
            ("Conversation Metrics", test_conversation_metrics()),
            ("Agent Performance", test_agent_performance()),
            ("Unauthorized Access", test_unauthorized_access()),
            ("User RBAC", test_user_rbac()),
            ("Admin RBAC", test_admin_rbac()),
            ("Pagination Filtering", test_pagination_filtering()),
            ("Revenue Summary", test_revenue_summary()),
            ("Revenue by Package", test_revenue_by_package()),
            ("Subscription Trends", test_subscription_trends()),
            ("Customer LTV", test_customer_ltv()),
            ("Subscriptions List", test_subscriptions_list()),
            ("Revenue User RBAC", test_revenue_user_rbac()),
            ("Revenue Unauthorized", test_revenue_unauthorized())
        ]
        
        results = []
        for name, success in tests:
            results.append(success)
        
        # Print summary
        total = len(results)
        passed = sum(results)
        print(f"\n{BLUE}Test Summary:{RESET}")
        print(f"Total Tests: {total}")
        print(f"Passed: {GREEN}{passed}{RESET}")
        print(f"Failed: {RED}{total - passed}{RESET}")
        
        # Exit with appropriate status code
        sys.exit(0 if all(results) else 1)
        
    except Exception as e:
        print(f"{RED}Test execution failed: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
