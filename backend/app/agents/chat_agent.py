"""ChatAgent implementation for handling AgentsFlowAI digital agency conversations.

This agent is responsible for engaging with potential clients, providing service
information, scheduling sessions, and qualifying leads.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid
from pydantic import BaseModel
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..utils.supabase_client import get_supabase_client
from ..models.manager import ModelManager
from ..utils.external_tools import check_calendar_availability as check_calendar_availability_tool, create_calendar_event, send_email, cancel_calendar_event

logger = logging.getLogger("agentsflowai.agents.chat")

# Service information for AgentsFlowAI
PIXELCRAFT_SERVICES = {
    "web_development": {
        "name": "Web Development",
        "description": "Custom website development with modern frameworks like React, Next.js, and Vue.",
        "features": [
            "Responsive design",
            "Performance optimization",
            "SEO-friendly architecture",
            "Modern UI/UX implementation"
        ],
        "starting_price": "$5,000"
    },
    "digital_marketing": {
        "name": "Digital Marketing",
        "description": "Comprehensive digital marketing strategies to grow your online presence.",
        "features": [
            "SEO optimization",
            "Content marketing",
            "Social media management",
            "Analytics and reporting"
        ],
        "starting_price": "$2,000/month"
    },
    "brand_design": {
        "name": "Brand Design",
        "description": "Professional brand identity design and visual storytelling.",
        "features": [
            "Logo design",
            "Brand guidelines",
            "Visual identity system",
            "Marketing collateral"
        ],
        "starting_price": "$3,500"
    },
    "ecommerce_solutions": {
        "name": "E-commerce Solutions",
        "description": "Full-service e-commerce development and optimization.",
        "features": [
            "Shopping cart integration",
            "Payment gateway setup",
            "Inventory management",
            "Mobile commerce optimization"
        ],
        "starting_price": "$7,500"
    },
    "content_creation": {
        "name": "Content Creation",
        "description": "High-quality content creation for all digital channels.",
        "features": [
            "Blog writing",
            "Social media content",
            "Email newsletters",
            "Video production"
        ],
        "starting_price": "$1,500/month"
    },
    "analytics_consulting": {
        "name": "Analytics Consulting",
        "description": "Data-driven insights and optimization strategies.",
        "features": [
            "Google Analytics setup",
            "Conversion tracking",
            "Performance monitoring",
            "ROI analysis"
        ],
        "starting_price": "$2,500/month"
    }
}

class AppointmentSlot(BaseModel):
    """Model for representing available appointment slots."""
    start_time: str
    end_time: str
    duration_minutes: int
    slot_type: str

async def get_services_info() -> Dict[str, Any]:
    """Tool function to retrieve AgentsFlowAI services information."""
    return PIXELCRAFT_SERVICES

async def check_availability(date: str, service_type: str) -> List[AppointmentSlot]:
    """Tool function to check appointment availability."""
    # Use external tool to check availability
    # Assuming date is YYYY-MM-DD, check business hours 09:00 to 17:00 UTC
    start_time = f"{date}T09:00:00Z"
    end_time = f"{date}T17:00:00Z"
    
    try:
        result = await check_calendar_availability_tool(start_time, end_time)
        
        if result["success"] and "available_slots" in result["data"]:
            # Convert available slots to AppointmentSlot objects
            slots = []
            for slot in result["data"]["available_slots"]:
                # Simple conversion, assuming we can book any time within the free slots
                # For simplicity, we'll just return the free slots as "available"
                # In a real app, we might chop these into 60-min chunks
                slots.append(AppointmentSlot(
                    start_time=slot["start"],
                    end_time=slot["end"],
                    duration_minutes=60, # Placeholder
                    slot_type=service_type
                ))
            return slots
        else:
            # Fallback to mock if external tool fails or returns no data
            logger.warning(f"Calendar check failed or returned no data: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error checking availability: {e}")

    # Fallback mock data
    mock_slots = [
        AppointmentSlot(
            start_time=f"{date}T09:00:00Z",
            end_time=f"{date}T10:00:00Z",
            duration_minutes=60,
            slot_type="strategy_session"
        ),
        AppointmentSlot(
            start_time=f"{date}T14:00:00Z",
            end_time=f"{date}T15:00:00Z",
            duration_minutes=60,
            slot_type="discovery_call"
        )
    ]
    return mock_slots

async def book_appointment(summary: str, start_time: str, end_time: str, email: str) -> Dict[str, Any]:
    """Tool function to book an appointment."""
    # Use external tool to create calendar event
    try:
        result = await create_calendar_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            attendees=[email],
            description="Scheduled via AgentsFlowAI Chat Assistant"
        )
        
        # Send confirmation email
        if result.get("success"):
            try:
                email_content = f"""
                <h1>Appointment Confirmed</h1>
                <p>Your appointment for <strong>{summary}</strong> has been scheduled.</p>
                <p><strong>Time:</strong> {start_time} - {end_time}</p>
                <p>A calendar invitation has been sent to your email.</p>
                <br>
                <p>Best regards,</p>
                <p>The AgentsFlowAI Team</p>
                """
                await send_email(
                    to_email=email,
                    subject="Appointment Confirmation - AgentsFlowAI",
                    html_content=email_content
                )
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {e}")
                
        return result
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        return {"success": False, "error": str(e)}

async def cancel_appointment(event_id: str, email: str) -> Dict[str, Any]:
    """Tool function to cancel an appointment."""
    try:
        result = await cancel_calendar_event(event_id)
        
        if result.get("success"):
            try:
                email_content = f"""
                <h1>Appointment Cancelled</h1>
                <p>Your appointment (ID: {event_id}) has been cancelled as requested.</p>
                <br>
                <p>Best regards,</p>
                <p>The AgentsFlowAI Team</p>
                """
                await send_email(
                    to_email=email,
                    subject="Appointment Cancellation - AgentsFlowAI",
                    html_content=email_content
                )
            except Exception as e:
                logger.error(f"Failed to send cancellation email: {e}")
                
        return result
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        return {"success": False, "error": str(e)}

def create_chat_agent(model_manager: Optional[ModelManager] = None) -> 'ChatAgent':
    """Factory function to create a ChatAgent instance with default configuration."""
    if model_manager is None:
        logger.warning("ModelManager not provided to ChatAgent, will use fallback responses")
    config = BaseAgentConfig(
        agent_id="agentsflowai_chat",
        name="AgentsFlowAI Chat Assistant",
        description="AI assistant for AgentsFlowAI digital marketing agency",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="""You are AgentsFlowAI's friendly AI assistant, helping potential clients
        learn about our digital marketing agency services. Focus on understanding client needs,
        providing accurate service information, and guiding them towards appropriate solutions.
        Always be professional, knowledgeable, and solution-oriented.""",
        capabilities=[
            "Answer questions about AgentsFlowAI services and pricing",
            "Provide detailed service information and use cases",
            "Schedule discovery calls and strategy sessions",
            "Qualify leads by understanding their needs and budget",
            "Maintain context throughout conversations",
            "Handle multi-turn interactions naturally"
        ],
        tools=[
            AgentTool(
                name="get_services_info",
                description="Get detailed information about AgentsFlowAI's services",
                function=get_services_info,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="check_availability",
                description="Check appointment availability for consultations",
                function=check_availability,
                parameters={"date": "str", "service_type": "str"},
                required_params=["date"]
            ),
            AgentTool(
                name="book_appointment",
                description="Book an appointment slot",
                function=book_appointment,
                parameters={"summary": "str", "start_time": "str", "end_time": "str", "email": "str"},
                required_params=["summary", "start_time", "end_time", "email"]
            ),
            AgentTool(
                name="cancel_appointment",
                description="Cancel an existing appointment",
                function=cancel_appointment,
                parameters={"event_id": "str", "email": "str"},
                required_params=["event_id", "email"]
            )
        ],
        task_type="chat",
        model_manager=model_manager
    )
    return ChatAgent(config)

class ChatAgent(BaseAgent):
    """ChatAgent for handling AgentsFlowAI client interactions."""

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process an incoming message and generate a response."""
        try:
            # Get or create conversation memory
            memory = self.get_memory(conversation_id)
            memory.add_message("user", message, metadata)

            # Check for shared memory context
            workflow_execution_id = metadata.get("workflow_execution_id") if metadata else None
            shared_context = None
            if workflow_execution_id:
                shared_context = await self.get_shared_memory(conversation_id, "workflow_context", scope="workflow", workflow_execution_id=workflow_execution_id)

            # Build conversation context
            context = memory.get_context_string(limit=5)
            if shared_context:
                context = f"Shared workflow context: {shared_context}\n\n{context}"
            system_prompt = self._build_system_prompt()

            # Generate response using ModelManager
            try:
                response = await self._generate_with_model(
                    prompt=context,
                    system_prompt=system_prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                assistant_message = response
                model_used = self.config.default_model # ModelManager doesn't return model name yet
            except Exception as e:
                logger.error(f"ModelManager failed for chat generation: {e}")
                # Fallback response on model failure
                assistant_message = "I apologize, but I'm currently unable to process your request due to AI model unavailability. Please try again later or contact support."
                model_used = None

            # Check if specialist help is needed
            specialist_needed = any(keyword in assistant_message.lower() or keyword in message.lower()
                                   for keyword in ["technical details", "pricing", "lead qualification", "specialist", "expert"])
            if specialist_needed and workflow_execution_id:
                # Determine target agent based on keywords
                target_agent = None
                if "technical" in (assistant_message + message).lower():
                    target_agent = "web_development"
                elif "pricing" in (assistant_message + message).lower() or "cost" in (assistant_message + message).lower():
                    target_agent = "service_recommendation"
                elif "lead" in (assistant_message + message).lower() or "qualification" in (assistant_message + message).lower():
                    target_agent = "lead_qualification"
                if target_agent:
                    from .orchestrator import orchestrator
                    conversation_context = context
                    await orchestrator.send_agent_message(
                        workflow_execution_id,
                        self.config.agent_id,
                        target_agent,
                        "handoff",
                        {"reason": "specialist_needed", "context": conversation_context}
                    )

            # Store key conversation insights in shared memory
            extracted_intent = message  # Simple extraction, could be improved
            if workflow_execution_id:
                await self.set_shared_memory(conversation_id, "user_intent", extracted_intent, scope="workflow", workflow_execution_id=workflow_execution_id)

            # Add response to memory
            memory.add_message("assistant", assistant_message)

            # Get Supabase client
            supabase = get_supabase_client()

            # Persist conversation and message to Supabase
            conversation_data = {
                "id": conversation_id,
                "status": "active",
                "channel": "chat",
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            message_data = {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": assistant_message,
                "agent_type": self.config.agent_id,
                "metadata": {},
                "created_at": datetime.utcnow().isoformat()
            }

            # Use upsert for conversation to handle existing conversations
            try:
                supabase.table("conversations").upsert(conversation_data).execute()
                supabase.table("messages").insert(message_data).execute()
            except Exception as e:
                logger.warning(f"Failed to persist message to Supabase: {e}")

            # Log the interaction
            await self._log_interaction(
                conversation_id=conversation_id,
                action="process_message",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )

            # Create and return agent response
            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "model_used": model_used,
                    "temperature": self.config.temperature,
                },
                tools_used=[],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            # Log error and raise
            await self._log_interaction(
                conversation_id=conversation_id,
                action="process_message",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise

    async def check_agent_messages(self, workflow_execution_id: str) -> List[Dict[str, Any]]:
        """Check for incoming agent messages in the workflow."""
        from .orchestrator import orchestrator
        messages = await orchestrator.get_agent_messages(self.config.agent_id, workflow_execution_id)
        # Process handoff messages
        for msg in messages:
            if msg["message_type"] == "handoff":
                self.logger.info(f"Received handoff from {msg['from_agent']}: {msg['content']}")
                # Could add logic to handle handoffs, e.g., update context
        return messages
