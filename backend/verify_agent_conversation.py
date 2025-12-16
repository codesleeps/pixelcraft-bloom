import requests
import json
import time

# Configuration
API_URL = "http://localhost:8000"
# API_URL = "https://api.agentsflowai.cloud" # Uncomment to test prod
HEADERS = {"Content-Type": "application/json"}

def run_test():
    print("--- 1. Creating Conversation (Local ID) ---")
    conversation_id = f"conv_{int(time.time())}"
    print(f"Conversation ID: {conversation_id}")

    print("\n--- 2. Executing Multi-Agent Workflow ---")
    payload = {
        "conversation_id": conversation_id,
        "workflow_type": "multi_agent",
        "participating_agents": ["chat", "service_recommendation", "lead_qualification"],
        "input_data": {
            "message": "I need a new website for my construction business. We want to accept payments online."
        },
        "workflow_config": {}
    }

    try:
        start_time = time.time()
        resp = requests.post(f"{API_URL}/api/agents/workflows/execute", json=payload, headers=HEADERS)
        resp.raise_for_status()
        result = resp.json()
        duration = time.time() - start_time
        
        print(f"Workflow ID: {result['workflow_id']}")
        print(f"Execution Time: {duration:.2f}s")
        print("\n--- Agent Responses ---")
        
        results = result.get("results", {})
        
        if "chat" in results:
            print("\n[Chat Agent]:")
            print(results["chat"].get("content", results["chat"]))
            
        if "recommendations" in results:
            print("\n[Recommendation Agent]:")
            rec_content = results["recommendations"].get("content", results["recommendations"])
            if isinstance(rec_content, dict):
                print(json.dumps(rec_content, indent=2))
            else:
                print(rec_content)

        if "lead_qualification" in results:
            print("\n[Lead Qualification Agent]:")
            lead_content = results["lead_qualification"].get("content", results["lead_qualification"])
            if isinstance(lead_content, dict):
                print(json.dumps(lead_content, indent=2))
            else:
                print(lead_content)

    except requests.exceptions.HTTPError as e:
        print(f"Workflow Failed: {e}")
        try:
            print(e.response.text)
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
