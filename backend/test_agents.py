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

from app.agents.orchestrator import orchestrator

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
        
        workflow_summary = {
            "chat_response": results["chat"]["content"][:100] + "...",
            "recommendations": len(json.loads(results["recommendations"]["content"])),
            "lead_score": json.loads(results["lead_qualification"]["content"]).get("score")
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
            ("Agent Routing", test_agent_routing())
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