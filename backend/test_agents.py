"""Agent system integration tests.

This module provides test functions to verify the functionality of all agents
and the orchestration system.
"""

import asyncio
import json
from datetime import datetime
import uuid
import sys
from typing import Any, Dict, Optional
import httpx

from app.agents.orchestrator import orchestrator
from app.utils.supabase_client import get_supabase_client

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
        print(json.dumps(data, indent=2))

async def test_chat_agent() -> bool:
    """Test the chat agent's basic response capability."""
    try:
        print_header("Testing Chat Agent")
        
        response = await orchestrator.invoke(
            "chat",
            {
                "message": "What services do you offer?",
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        result = response.to_dict()
        print_result("Chat Response", True, {
            "content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
        })
        return True
        
    except Exception as e:
        print_result("Chat Agent Test", False, {"error": str(e)})
        return False

async def test_lead_qualification() -> bool:
    """Test lead qualification agent with sample lead data."""
    try:
        print_header("Testing Lead Qualification Agent")
        
        lead_data = {
            "id": str(uuid.uuid4()),
            "company": "TechGrowth Solutions",
            "budget_range": "10000-25000",
            "timeline": "immediate",
            "services_interested": ["digital_marketing", "content_creation"],
            "notes": """We're looking to improve our online presence significantly. 
            Need help with SEO optimization and social media management. 
            We want to start as soon as possible and have allocated a budget 
            of $20,000 for the initial phase."""
        }
        
        response = await orchestrator.invoke(
            "lead_qualification",
            {
                "message": lead_data["notes"],
                "lead_data": lead_data,
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        result = response.to_dict()
        print_result("Lead Qualification", True, {
            "score": json.loads(result["content"]).get("score"),
            "priority": json.loads(result["content"]).get("priority"),
            "suggested_actions": json.loads(result["content"]).get("suggested_actions")
        })
        return True
        
    except Exception as e:
        print_result("Lead Qualification Test", False, {"error": str(e)})
        return False

async def test_recommendation_agent() -> bool:
    """Test service recommendation agent."""
    try:
        print_header("Testing Service Recommendation Agent")
        
        message = """We're a growing e-commerce business looking to increase our 
        online visibility and customer engagement. We need help with digital 
        marketing and possibly website optimization. Our main goals are to 
        improve search rankings and social media presence."""
        
        response = await orchestrator.invoke(
            "service_recommendation",
            {
                "message": message,
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        result = response.to_dict()
        print_result("Service Recommendations", True, {
            "recommendations": json.loads(result["content"])[:2]  # Show first 2 recommendations
        })
        return True
        
    except Exception as e:
        print_result("Recommendation Agent Test", False, {"error": str(e)})
        return False

async def test_multi_agent_workflow() -> bool:
    """Test the complete multi-agent workflow."""
    try:
        print_header("Testing Multi-Agent Workflow")
        
        conversation_id = str(uuid.uuid4())
        input_data = {
            "message": """We need help with our digital marketing strategy. 
            We have a budget of $15,000 and want to focus on SEO and social media. 
            Our company is in the B2B software sector.""",
            "metadata": {
                "company": "SaaS Solutions Inc",
                "industry": "B2B Software",
                "budget_range": "10000-25000",
                "timeline": "1-3_months"
            }
        }
        
        results = await orchestrator.multi_agent_workflow(
            input_data=input_data,
            conversation_id=conversation_id,
            run_chat=True,
            run_recommendations=True,
            run_lead_analysis=True
        )
        
        # Verify workflow_id is returned
        workflow_id = results.get("workflow_id")
        if not workflow_id:
            print_result("Multi-Agent Workflow", False, {"error": "workflow_id not returned"})
            return False
        
        # Check workflow state is 'completed'
        supabase = get_supabase_client()
        workflow_result = await supabase.table("workflow_executions").select("current_state").eq("id", workflow_id).execute()
        if not workflow_result.data or workflow_result.data[0]["current_state"] != "completed":
            print_result("Multi-Agent Workflow", False, {"error": "workflow not completed"})
            return False
        
        # Verify shared memory contains expected keys
        memory_keys = await supabase.table("shared_memory").select("memory_key").eq("conversation_id", conversation_id).eq("scope", "workflow").execute()
        expected_keys = ["chat_result", "recommendations_result", "lead_qualification_result"]
        actual_keys = [item["memory_key"] for item in memory_keys.data]
        if not all(key in actual_keys for key in expected_keys):
            print_result("Multi-Agent Workflow", False, {"error": f"missing shared memory keys, expected {expected_keys}, got {actual_keys}"})
            return False
        
        workflow_summary = {
            "chat_response": results["chat"]["content"][:100] + "...",
            "recommendations": len(json.loads(results["recommendations"]["content"])),
            "lead_score": json.loads(results["lead_qualification"]["content"]).get("score"),
            "workflow_id": workflow_id
        }
        
        print_result("Multi-Agent Workflow", True, workflow_summary)
        return True
        
    except Exception as e:
        print_result("Multi-Agent Workflow Test", False, {"error": str(e)})
        return False

async def test_agent_routing() -> bool:
    """Test message routing to appropriate agents."""
    try:
        print_header("Testing Agent Routing")
        
        test_messages = [
            ("What are your services?", "chat"),
            ("Can you qualify this lead?", "lead_qualification"),
            ("What services would you recommend?", "service_recommendation")
        ]
        
        results = []
        for message, expected_agent in test_messages:
            response = await orchestrator.route_message(
                message=message,
                conversation_id=str(uuid.uuid4())
            )
            routed_to = response.agent_id
            success = routed_to == expected_agent
            results.append({
                "message": message,
                "expected": expected_agent,
                "routed_to": routed_to,
                "correct": success
            })
        
        all_correct = all(r["correct"] for r in results)
        print_result("Message Routing", all_correct, {"routes": results})
        return all_correct
        
    except Exception as e:
        print_result("Agent Routing Test", False, {"error": str(e)})
        return False

async def test_conditional_workflow() -> bool:
    """Test conditional routing based on lead score."""
    try:
        print_header("Testing Conditional Workflow")
        
        conversation_id = str(uuid.uuid4())
        routing_rules = {
            "conditions": [
                {"field": "metadata.lead_score", "operator": ">", "value": 70, "next_agent": "web_development"}
            ],
            "default": "chat"
        }
        input_data = {
            "message": "We need website development help with high budget."
        }
        
        results = await orchestrator.conditional_workflow(
            conversation_id=conversation_id,
            initial_agent="lead_qualification",
            routing_rules=routing_rules,
            input_data=input_data
        )
        
        workflow_id = results.get("workflow_id")
        execution_path = results.get("execution_path", [])
        
        # Verify correct agent invoked based on conditions
        # Assuming lead score > 70 for this input
        expected_path = ["lead_qualification", "web_development"]
        if execution_path != expected_path:
            print_result("Conditional Workflow", False, {"error": f"execution path mismatch, expected {expected_path}, got {execution_path}"})
            return False
        
        # Check workflow state
        supabase = get_supabase_client()
        workflow_result = await supabase.table("workflow_executions").select("current_state").eq("id", workflow_id).execute()
        if not workflow_result.data or workflow_result.data[0]["current_state"] != "completed":
            print_result("Conditional Workflow", False, {"error": "workflow not completed"})
            return False
        
        # Verify shared memory accessible
        memory_keys = await supabase.table("shared_memory").select("memory_key").eq("conversation_id", conversation_id).eq("scope", "workflow").execute()
        expected_keys = ["lead_qualification_result", "web_development_result"]
        actual_keys = [item["memory_key"] for item in memory_keys.data]
        if not all(key in actual_keys for key in expected_keys):
            print_result("Conditional Workflow", False, {"error": f"missing shared memory keys, expected {expected_keys}, got {actual_keys}"})
            return False
        
        print_result("Conditional Workflow", True, {"execution_path": execution_path, "workflow_id": workflow_id})
        return True
        
    except Exception as e:
        print_result("Conditional Workflow Test", False, {"error": str(e)})
        return False

async def test_agent_messaging() -> bool:
    """Test sending messages between agents."""
    try:
        print_header("Testing Agent Messaging")
        
        conversation_id = str(uuid.uuid4())
        workflow_id = await orchestrator.create_workflow_execution(
            conversation_id, "test", ["chat", "lead_qualification"], {}, {}
        )
        
        # Send message from chat to lead_qualification
        message_id = await orchestrator.send_agent_message(
            workflow_execution_id=workflow_id,
            from_agent="chat",
            to_agent="lead_qualification",
            message_type="request",
            content={"request": "qualify this lead"},
            metadata={"priority": "high"}
        )
        
        # Get messages for lead_qualification
        messages = await orchestrator.get_agent_messages("lead_qualification", workflow_id)
        if not messages or messages[0]["id"] != message_id:
            print_result("Agent Messaging", False, {"error": "message not delivered"})
            return False
        
        # Check message status in database
        supabase = get_supabase_client()
        msg_result = await supabase.table("agent_messages").select("status").eq("id", message_id).execute()
        if not msg_result.data or msg_result.data[0]["status"] != "processed":
            print_result("Agent Messaging", False, {"error": "message status not updated"})
            return False
        
        print_result("Agent Messaging", True, {"message_id": message_id, "messages_received": len(messages)})
        return True
        
    except Exception as e:
        print_result("Agent Messaging Test", False, {"error": str(e)})
        return False

async def test_shared_memory() -> bool:
    """Test setting and getting shared memory across agents."""
    try:
        print_header("Testing Shared Memory")
        
        conversation_id = str(uuid.uuid4())
        workflow_id = await orchestrator.create_workflow_execution(
            conversation_id, "test", ["chat"], {}, {}
        )
        
        chat_agent = orchestrator.get("chat")
        
        # Set shared memory
        test_data = {"user_intent": "website development", "confidence": 0.9}
        await chat_agent.set_shared_memory(conversation_id, "test_key", test_data, scope="workflow", workflow_execution_id=workflow_id)
        
        # Get shared memory
        retrieved = await chat_agent.get_shared_memory(conversation_id, "test_key", scope="workflow", workflow_execution_id=workflow_id)
        if retrieved != test_data:
            print_result("Shared Memory", False, {"error": "data mismatch"})
            return False
        
        # Check access_count incremented
        supabase = get_supabase_client()
        memory_result = await supabase.table("shared_memory").select("access_count").eq("conversation_id", conversation_id).eq("memory_key", "test_key").eq("scope", "workflow").execute()
        if not memory_result.data or memory_result.data[0]["access_count"] != 1:
            print_result("Shared Memory", False, {"error": "access_count not incremented"})
            return False
        
        # Test different scopes
        await chat_agent.set_shared_memory(conversation_id, "global_key", {"global": True}, scope="global")
        global_data = await chat_agent.get_shared_memory(conversation_id, "global_key", scope="global")
        if global_data != {"global": True}:
            print_result("Shared Memory", False, {"error": "global scope failed"})
            return False
        
        # Test expiration (set with past date)
        expired_at = datetime.utcnow().replace(year=2000)
        await chat_agent.set_shared_memory(conversation_id, "expired_key", {"expired": True}, scope="conversation", expires_at=expired_at)
        expired_data = await chat_agent.get_shared_memory(conversation_id, "expired_key", scope="conversation")
        if expired_data is not None:
            print_result("Shared Memory", False, {"error": "expired data not filtered"})
            return False
        
        print_result("Shared Memory", True, {"test_data": test_data, "global_data": global_data})
        return True
        
    except Exception as e:
        print_result("Shared Memory Test", False, {"error": str(e)})
        return False

async def test_workflow_visualization() -> bool:
    """Test workflow visualization endpoint."""
    try:
        print_header("Testing Workflow Visualization")
        
        conversation_id = str(uuid.uuid4())
        input_data = {
            "message": "We need digital marketing help."
        }
        
        results = await orchestrator.multi_agent_workflow(
            input_data=input_data,
            conversation_id=conversation_id,
            run_chat=True,
            run_recommendations=True,
            run_lead_analysis=True
        )
        
        workflow_id = results["workflow_id"]
        
        # Query workflow visualization endpoint
        async with httpx.AsyncClient() as client:
            # Assuming server is running on localhost:8000, adjust as needed
            response = await client.get(f"http://localhost:8000/api/agents/workflows/{workflow_id}/visualization")
            if response.status_code != 200:
                print_result("Workflow Visualization", False, {"error": f"endpoint returned {response.status_code}"})
                return False
            
            data = response.json()
            
            # Verify execution timeline
            timeline = data.get("execution_timeline", [])
            if not timeline or len(timeline) < 3:  # At least pending, running, completed
                print_result("Workflow Visualization", False, {"error": "execution timeline incomplete"})
                return False
            
            # Verify agent interactions
            interactions = data.get("agent_interactions", [])
            if not interactions:  # Should have some interactions
                print_result("Workflow Visualization", False, {"error": "no agent interactions"})
                return False
            
            # Check execution graph
            graph = data.get("execution_graph", {})
            if not graph.get("nodes") or not graph.get("edges"):
                print_result("Workflow Visualization", False, {"error": "execution graph incomplete"})
                return False
            
            # Verify shared memory keys
            shared_keys = data.get("shared_memory_keys", [])
            expected_keys = ["chat_result", "recommendations_result", "lead_qualification_result"]
            if not all(key in shared_keys for key in expected_keys):
                print_result("Workflow Visualization", False, {"error": f"missing shared memory keys, expected {expected_keys}, got {shared_keys}"})
                return False
        
        print_result("Workflow Visualization", True, {"timeline_events": len(timeline), "interactions": len(interactions), "shared_keys": shared_keys})
        return True
        
    except Exception as e:
        print_result("Workflow Visualization Test", False, {"error": str(e)})
        return False

async def main() -> None:
    """Run all agent tests."""
    try:
        print_header("PixelCraft AI Agent System Tests")
        
        # List registered agents
        agents = orchestrator.list_agents()
        print(f"Registered Agents: {', '.join(agents)}\n")
        
        # Run all tests
        tests = [
            ("Chat Agent", test_chat_agent()),
            ("Lead Qualification", test_lead_qualification()),
            ("Service Recommendation", test_recommendation_agent()),
            ("Multi-Agent Workflow", test_multi_agent_workflow()),
            ("Agent Routing", test_agent_routing()),
            ("Conditional Workflow", test_conditional_workflow()),
            ("Agent Messaging", test_agent_messaging()),
            ("Shared Memory", test_shared_memory()),
            ("Workflow Visualization", test_workflow_visualization())
        ]
        
        results = []
        for name, test_coro in tests:
            try:
                success = await test_coro
                results.append(success)
            except Exception as e:
                print(f"{RED}Error in {name}: {str(e)}{RESET}")
                results.append(False)
        
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
    asyncio.run(main())