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
from ..utils.redis_client import publish_analytics_event
from ..utils.notification_service import create_notification, create_notification_for_admins
from ..models.manager import ModelManager

logger = logging.getLogger("agentsflowai.agents.orchestrator")

class AgentOrchestrator:
    """Orchestrates multiple agents, handling routing and workflows."""

    def __init__(self):
        self.registry: Dict[str, BaseAgent] = {}
        self.message_bus: Dict[str, List[Dict[str, Any]]] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
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

    async def send_agent_message(
        self,
        workflow_execution_id: str,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send a message from one agent to another within a workflow."""
        if from_agent not in self.registry or to_agent not in self.registry:
            raise ValueError(f"Invalid agents: from_agent '{from_agent}' or to_agent '{to_agent}' not registered")

        supabase = get_supabase_client()
        message_data = {
            "workflow_execution_id": workflow_execution_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            "status": "pending",
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        result = await supabase.table("agent_messages").insert(message_data).execute()
        message_id = result.data[0]["id"]

        # Add to in-memory message bus for immediate delivery
        self.message_bus.setdefault(to_agent, []).append(message_data)

        self.logger.info(f"Sent agent message from {from_agent} to {to_agent} in workflow {workflow_execution_id}")
        return message_id

    async def get_agent_messages(
        self,
        agent_id: str,
        workflow_execution_id: Optional[str] = None,
        mark_as_processed: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve pending messages for an agent."""
        messages = self.message_bus.get(agent_id, [])
        if workflow_execution_id:
            messages = [msg for msg in messages if msg["workflow_execution_id"] == workflow_execution_id]

        if mark_as_processed and messages:
            supabase = get_supabase_client()
            message_ids = [msg["id"] for msg in messages]
            await supabase.table("agent_messages").update({
                "status": "processed",
                "processed_at": datetime.utcnow().isoformat()
            }).in_("id", message_ids).execute()
            # Clear from message bus
            self.message_bus[agent_id] = [msg for msg in self.message_bus[agent_id] if msg not in messages]

        return messages

    async def create_workflow_execution(
        self,
        conversation_id: str,
        workflow_type: str,
        participating_agents: List[str],
        workflow_config: Dict[str, Any],
        execution_plan: Dict[str, Any]
    ) -> str:
        """Create a new workflow execution record."""
        supabase = get_supabase_client()
        workflow_data = {
            "conversation_id": conversation_id,
            "workflow_type": workflow_type,
            "current_state": "pending",
            "participating_agents": participating_agents,
            "workflow_config": workflow_config,
            "execution_plan": execution_plan,
            "started_at": datetime.utcnow().isoformat()
        }
        result = await supabase.table("workflow_executions").insert(workflow_data).execute()
        workflow_id = result.data[0]["id"]

        self.active_workflows[workflow_id] = workflow_data

        publish_analytics_event("analytics:workflows", "workflow_created", {
            "workflow_id": workflow_id,
            "conversation_id": conversation_id
        })

        self.logger.info(f"Created workflow execution {workflow_id} for conversation {conversation_id}")
        return workflow_id

    async def update_workflow_state(
        self,
        workflow_execution_id: str,
        current_state: str,
        current_step: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update the state of a workflow execution."""
        supabase = get_supabase_client()
        update_data = {
            "current_state": current_state,
            "updated_at": datetime.utcnow().isoformat()
        }
        if current_step:
            update_data["current_step"] = current_step
        if results:
            update_data["results"] = results
        if error_message:
            update_data["error_message"] = error_message
        if current_state in ["completed", "failed"]:
            update_data["completed_at"] = datetime.utcnow().isoformat()

        await supabase.table("workflow_executions").update(update_data).eq("id", workflow_execution_id).execute()

        if workflow_execution_id in self.active_workflows:
            self.active_workflows[workflow_execution_id].update(update_data)

        publish_analytics_event("analytics:workflows", "workflow_state_update", {
            "workflow_id": workflow_execution_id,
            "current_state": current_state,
            "current_step": current_step
        })

        # Create notifications for workflow state changes
        try:
            if current_state == "completed":
                conversation = await supabase.table("conversations").select("user_id").eq("id", self.active_workflows[workflow_execution_id]["conversation_id"]).single().execute()
                if conversation.data and conversation.data[0].get("user_id"):
                    await create_notification(
                        recipient_id=conversation.data[0]["user_id"],
                        notification_type="workflow",
                        severity="success",
                        title="Workflow Completed",
                        message=f"Workflow {workflow_execution_id} has completed successfully",
                        action_url=f"/dashboard/workflows/{workflow_execution_id}",
                        metadata={"workflow_id": workflow_execution_id, "workflow_type": self.active_workflows[workflow_execution_id]["workflow_type"]}
                    )
            elif current_state == "failed":
                conversation = await supabase.table("conversations").select("user_id").eq("id", self.active_workflows[workflow_execution_id]["conversation_id"]).single().execute()
                if conversation.data and conversation.data[0].get("user_id"):
                    await create_notification(
                        recipient_id=conversation.data[0]["user_id"],
                        notification_type="workflow",
                        severity="error",
                        title="Workflow Failed",
                        message=f"Workflow {workflow_execution_id} has failed: {error_message}",
                        action_url=f"/dashboard/workflows/{workflow_execution_id}",
                        metadata={"workflow_id": workflow_execution_id, "workflow_type": self.active_workflows[workflow_execution_id]["workflow_type"], "error": error_message}
                    )
        except Exception as e:
            self.logger.warning(f"Failed to create workflow notification: {e}")

        self.logger.info(f"Updated workflow {workflow_execution_id} state to {current_state}")

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

            # Create notifications for critical agent errors
            try:
                if error and agent_id in ["lead_qualification", "web_development"]:
                    await create_notification_for_admins(
                        notification_type="agent",
                        severity="error",
                        title=f"Agent {agent_id} Failed",
                        message=f"Agent {agent_id} encountered an error: {error}",
                        metadata={"agent_id": agent_id, "conversation_id": conversation_id, "error": error}
                    )
            except Exception as e:
                self.logger.warning(f"Failed to create agent error notification: {e}")

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
        """Execute a multi-agent workflow with state tracking and shared memory."""
        results = {}
        message = input_data.get("message", "")
        workflow_id = await self.create_workflow_execution(
            conversation_id, "multi_agent", ["chat", "service_recommendation", "lead_qualification"], {}, {}
        )
        await self.update_workflow_state(workflow_id, "running", "chat")

        try:
            # Step 1: Chat interaction
            if run_chat:
                self.logger.info(f"Running chat agent for conversation {conversation_id}")
                await self.update_workflow_state(workflow_id, "running", "chat")
                chat_agent = self.get("chat")
                chat_response = await chat_agent.process_message(conversation_id, message, {"workflow_execution_id": workflow_id})
                results["chat"] = chat_response.to_dict()
                await chat_agent.set_shared_memory(conversation_id, "chat_result", chat_response.to_dict(), scope="workflow", workflow_execution_id=workflow_id)

            # Step 2: Service recommendations
            if run_recommendations:
                self.logger.info(f"Running recommendation agent for conversation {conversation_id}")
                await self.update_workflow_state(workflow_id, "running", "service_recommendation")
                rec_agent = self.get("service_recommendation")
                rec_response = await rec_agent.process_message(conversation_id, message, {"workflow_execution_id": workflow_id})
                results["recommendations"] = rec_response.to_dict()
                await rec_agent.set_shared_memory(conversation_id, "recommendations_result", rec_response.to_dict(), scope="workflow", workflow_execution_id=workflow_id)

            # Step 3: Lead qualification
            if run_lead_analysis:
                self.logger.info(f"Running lead qualification for conversation {conversation_id}")
                await self.update_workflow_state(workflow_id, "running", "lead_qualification")
                lead_agent = self.get("lead_qualification")
                lead_response = await lead_agent.process_message(conversation_id, message, {"workflow_execution_id": workflow_id})
                results["lead_qualification"] = lead_response.to_dict()
                await lead_agent.set_shared_memory(conversation_id, "lead_qualification_result", lead_response.to_dict(), scope="workflow", workflow_execution_id=workflow_id)

            await self.update_workflow_state(workflow_id, "completed", results=results)
            results["workflow_id"] = workflow_id
            return results

        except Exception as e:
            self.logger.exception("Multi-agent workflow failed")
            await self.update_workflow_state(workflow_id, "failed", error_message=str(e))
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

    async def conditional_workflow(
        self,
        conversation_id: str,
        initial_agent: str,
        routing_rules: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a conditional workflow with dynamic routing."""
        results = {}
        execution_path = []
        workflow_id = await self.create_workflow_execution(
            conversation_id, "conditional", [initial_agent], routing_rules, {}
        )
        await self.update_workflow_state(workflow_id, "running", initial_agent)
        current_agent = initial_agent
        max_steps = 10
        step = 0

        try:
            while current_agent and step < max_steps:
                execution_path.append(current_agent)
                agent = self.get(current_agent)
                if not agent:
                    raise ValueError(f"Agent {current_agent} not found")

                response = await agent.process_message(conversation_id, input_data.get("message", ""), {
                    "workflow_execution_id": workflow_id
                })
                results[current_agent] = response.to_dict()
                await agent.set_shared_memory(conversation_id, f"{current_agent}_result", response.to_dict(), scope="workflow", workflow_execution_id=workflow_id)

                # Evaluate routing rules
                next_agent = None
                for condition in routing_rules.get("conditions", []):
                    field = condition["field"]
                    operator = condition["operator"]
                    value = condition["value"]
                    next_candidate = condition["next_agent"]
                    response_value = response.metadata.get(field.split(".")[-1]) if "." in field else response.metadata.get(field)
                    if self._evaluate_condition(response_value, operator, value):
                        next_agent = next_candidate
                        break
                if not next_agent:
                    next_agent = routing_rules.get("default")

                current_agent = next_agent
                step += 1

            await self.update_workflow_state(workflow_id, "completed", results=results)
            return {"results": results, "execution_path": execution_path, "workflow_id": workflow_id}

        except Exception as e:
            self.logger.exception("Conditional workflow failed")
            await self.update_workflow_state(workflow_id, "failed", error_message=str(e))
            raise

    def _evaluate_condition(self, response_value: Any, operator: str, value: Any) -> bool:
        """Evaluate a simple condition for routing."""
        if operator == ">":
            return response_value > value
        elif operator == "<":
            return response_value < value
        elif operator == "==":
            return response_value == value
        elif operator == "!=":
            return response_value != value
        return False

# Create global orchestrator instance
orchestrator = AgentOrchestrator()

def initialize_agents(model_manager: Optional[ModelManager] = None) -> None:
    """Initialize and register all agents.

    If a ModelManager instance is provided it will be passed to agents that
    support it (so they can use available models for generation).
    """
    try:
        # Create agents (pass model_manager where supported)
        chat_agent = create_chat_agent(model_manager)
        lead_agent = create_lead_qualification_agent(model_manager)
        rec_agent = create_recommendation_agent(model_manager)
        web_dev_agent = create_web_development_agent(model_manager)
        # digital_marketing agent factory does not accept model_manager
        digital_marketing_agent = create_digital_marketing_agent()
        brand_design_agent = create_brand_design_agent(model_manager)
        ecommerce_agent = create_ecommerce_solutions_agent(model_manager)
        content_creation_agent = create_content_creation_agent(model_manager)
        analytics_agent = create_analytics_consulting_agent(model_manager)

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
# initialize_agents()  # Moved to main.py startup event to avoid circular imports

