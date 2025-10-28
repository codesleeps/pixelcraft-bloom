"""Agent orchestration module.

This module provides the orchestrator for managing and coordinating multiple agents,
handling agent routing, workflow execution, and error recovery.
"""

from typing import Dict, Any, List, Optional
import time
import asyncio
import logging
from datetime import datetime

from .base import BaseAgent, AgentResponse
from .chat_agent import create_chat_agent
from .lead_agent import create_lead_qualification_agent
from .recommendation_agent import create_recommendation_agent
from .web_development_agent import create_web_development_agent
from .digital_marketing_agent import create_digital_marketing_agent
from .brand_design_agent import create_brand_design_agent
from .ecommerce_solutions_agent import create_ecommerce_solutions_agent
from .content_creation_agent import create_content_creation_agent
from .analytics_consulting_agent import create_analytics_consulting_agent
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger("pixelcraft.agents.orchestrator")

class AgentOrchestrator:
    """Orchestrates multiple agents, handling routing and workflows."""

    def __init__(self):
        self.registry: Dict[str, BaseAgent] = {}
        self.logger = logger

    def register(self, agent_id: str, agent: BaseAgent) -> None:
        """Register an agent in the orchestrator."""
        self.registry[agent_id] = agent
        self.logger.info(f"Registered agent: {agent_id}")

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.registry.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self.registry.keys())

    async def invoke(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> AgentResponse:
        """Invoke an agent with timing and error handling."""
        agent = self.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        start_time = time.time()
        error = None

        try:
            # Extract message and metadata
            message = input_data.get("message", "")
            metadata = {k: v for k, v in input_data.items() if k != "message"}

            # Process message
            response = await agent.process_message(
                conversation_id=conversation_id or "",
                message=message,
                metadata=metadata
            )

            return response

        except Exception as e:
            error = str(e)
            self.logger.exception(f"Agent {agent_id} invocation failed")
            raise
        finally:
            # Log execution metrics
            execution_time = time.time() - start_time
            try:
                supabase = get_supabase_client()
                await supabase.table("agent_logs").insert({
                    "agent_type": agent_id,
                    "conversation_id": conversation_id,
                    "action": "invoke",
                    "input_data": input_data,
                    "execution_time_ms": round(execution_time * 1000),
                    "status": "error" if error else "success",
                    "error_message": error,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except Exception as e:
                self.logger.error(f"Failed to log agent metrics: {e}")

    async def route_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Route a message to the appropriate agent based on content."""
        # Convert message to lowercase for matching
        message_lower = message.lower()

        # Define routing keywords
        routing_rules = {
            "lead_qualification": [
                "score", "qualify", "qualification", "evaluate",
                "assessment", "analyze lead", "lead score"
            ],
            "service_recommendation": [
                "recommend", "suggestion", "service", "which service",
                "what service", "best option", "solution"
            ],
            "web_development": [
                "website", "web development", "frontend", "backend",
                "react", "vue", "angular", "full-stack", "cms"
            ],
            "digital_marketing": [
                "marketing", "seo", "advertising", "campaign",
                "social media", "content marketing", "ppc", "roi"
            ],
            "brand_design": [
                "brand", "logo", "design", "visual identity",
                "branding", "creative", "packaging"
            ],
            "ecommerce_solutions": [
                "ecommerce", "shopify", "woocommerce", "online store",
                "shopping cart", "payment", "inventory"
            ],
            "content_creation": [
                "content", "writing", "blog", "copywriting",
                "social media content", "video", "newsletter"
            ],
            "analytics_consulting": [
                "analytics", "data", "tracking", "metrics",
                "google analytics", "reporting", "insights"
            ]
        }

        # Find matching agent based on keywords
        target_agent = "chat"  # Default to chat agent
        for agent_id, keywords in routing_rules.items():
            if any(keyword in message_lower for keyword in keywords):
                target_agent = agent_id
                break

        # Prepare input data
        input_data = {
            "message": message,
            **(metadata or {})
        }

        # Invoke the selected agent
        return await self.invoke(target_agent, input_data, conversation_id)

    async def multi_agent_workflow(
        self,
        input_data: Dict[str, Any],
        conversation_id: str,
        run_chat: bool = True,
        run_recommendations: bool = True,
        run_lead_analysis: bool = True
    ) -> Dict[str, Any]:
        """Execute a multi-agent workflow."""
        results = {}
        message = input_data.get("message", "")

        try:
            # Step 1: Chat interaction
            if run_chat:
                self.logger.info(f"Running chat agent for conversation {conversation_id}")
                chat_response = await self.invoke(
                    "chat",
                    {"message": message},
                    conversation_id
                )
                results["chat"] = chat_response.to_dict()

            # Step 2: Service recommendations
            if run_recommendations:
                self.logger.info(f"Running recommendation agent for conversation {conversation_id}")
                rec_response = await self.invoke(
                    "service_recommendation",
                    {
                        "message": message,
                        "chat_response": results.get("chat", {})
                    },
                    conversation_id
                )
                results["recommendations"] = rec_response.to_dict()

            # Step 3: Lead qualification
            if run_lead_analysis:
                self.logger.info(f"Running lead qualification for conversation {conversation_id}")
                qual_response = await self.invoke(
                    "lead_qualification",
                    {
                        "message": message,
                        "chat_response": results.get("chat", {}),
                        "recommendations": results.get("recommendations", {})
                    },
                    conversation_id
                )
                results["lead_qualification"] = qual_response.to_dict()

            return results

        except Exception as e:
            self.logger.exception("Multi-agent workflow failed")
            # Log workflow failure
            try:
                supabase = get_supabase_client()
                await supabase.table("agent_logs").insert({
                    "agent_type": "workflow",
                    "conversation_id": conversation_id,
                    "action": "multi_agent_workflow",
                    "input_data": input_data,
                    "status": "error",
                    "error_message": str(e),
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except Exception as log_error:
                self.logger.error(f"Failed to log workflow error: {log_error}")
            raise

# Create global orchestrator instance
orchestrator = AgentOrchestrator()

def initialize_agents() -> None:
    """Initialize and register all agents."""
    try:
        # Create agents
        chat_agent = create_chat_agent()
        lead_agent = create_lead_qualification_agent()
        rec_agent = create_recommendation_agent()
        web_dev_agent = create_web_development_agent()
        digital_marketing_agent = create_digital_marketing_agent()
        brand_design_agent = create_brand_design_agent()
        ecommerce_agent = create_ecommerce_solutions_agent()
        content_creation_agent = create_content_creation_agent()
        analytics_agent = create_analytics_consulting_agent()

        # Register agents
        orchestrator.register("chat", chat_agent)
        orchestrator.register("lead_qualification", lead_agent)
        orchestrator.register("service_recommendation", rec_agent)
        orchestrator.register("web_development", web_dev_agent)
        orchestrator.register("digital_marketing", digital_marketing_agent)
        orchestrator.register("brand_design", brand_design_agent)
        orchestrator.register("ecommerce_solutions", ecommerce_agent)
        orchestrator.register("content_creation", content_creation_agent)
        orchestrator.register("analytics_consulting", analytics_agent)

        logger.info("Successfully initialized all agents")

    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        raise

# Initialize agents when module is imported
initialize_agents()
