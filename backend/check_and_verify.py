import requests
import json
import os

# Configuration
API_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def check_table_visibility():
    # We can't directly check table visibility via public API easily unless we have an endpoint that just list workflows.
    # Fortunately we do: GET /api/agents/workflows
    
    print("--- Checking Workflow Table Visibility ---")
    try:
        resp = requests.get(f"{API_URL}/api/agents/workflows?limit=1", headers=HEADERS)
        if resp.status_code == 200:
            print("SUCCESS: Table `workflow_executions` is visible and accessible.")
            return True
        else:
            print(f"FAILURE: API returned {resp.status_code}")
            print(resp.text)
            return False
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return False

if __name__ == "__main__":
    if check_table_visibility():
        # Proceed with execution test
        print("\n--- Running Conversation Test ---")
        # Ensure we have the verify_agent_conversation.py module or code to run
        try:
            import verify_agent_conversation
            verify_agent_conversation.run_test()
        except ImportError:
            print("Could not import verification script, but table check passed.")
