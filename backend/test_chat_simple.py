import requests
import json
import time
import uuid

# Configuration
API_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def run_test():
    conversation_id = str(uuid.uuid4())
    print(f"Conversation ID: {conversation_id}")

    print("\n--- Testing Chat Agent Only (with Lead Data Stub) ---")
    payload = {
        "conversation_id": conversation_id,
        "workflow_type": "multi_agent",
        "participating_agents": ["chat"],
        "input_data": {
            "message": "Hello, I am interested in building a website. Can you help?",
            "lead_data": {
                "budget_range": "5000-10000",
                "timeline": "1-3_months",
                "company": "Test Corp",
                "notes": "Interested in AI chatbot integration.",
                "services_interested": ["web_development", "ai_integration"]
            }
        },
        "workflow_config": {}
    }

    try:
        resp = requests.post(f"{API_URL}/api/agents/workflows/execute", json=payload, headers=HEADERS)
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code} - {resp.text}")
            return
            
        result = resp.json()
        print(f"Workflow ID: {result.get('workflow_id')}")
        
        results = result.get("results", {})
        if "chat" in results:
            content = results["chat"].get("content", results["chat"])
            print("\n[AI RESPONSE]:")
            print(content)
        else:
            print("No chat response in results:", results.keys())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
