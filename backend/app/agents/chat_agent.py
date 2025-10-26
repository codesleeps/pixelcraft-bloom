"""ChatAgent implementation for handling PixelCraft digital agency conversations.

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
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger("pixelcraft.agents.chat")

# Service information for PixelCraft
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
    """Tool function to retrieve PixelCraft services information."""
    return PIXELCRAFT_SERVICES

async def check_availability(date: str, service_type: str) -> List[AppointmentSlot]:
    """Tool function to check appointment availability."""
    # TODO: Implement actual calendar integration
    # For now, return mock data
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

def create_chat_agent() -> 'ChatAgent':
    """Factory function to create a ChatAgent instance with default configuration."""
    config = BaseAgentConfig(
        agent_id="pixelcraft_chat",
        name="PixelCraft Chat Assistant",
        description="AI assistant for PixelCraft digital marketing agency",
        default_model="llama2",  # or other model configured in Ollama
        temperature=0.7,
        max_tokens=1000,
        system_prompt="""You are PixelCraft's friendly AI assistant, helping potential clients 
        learn about our digital marketing agency services. Focus on understanding client needs,
        providing accurate service information, and guiding them towards appropriate solutions.
        Always be professional, knowledgeable, and solution-oriented.""",
        capabilities=[
            "Answer questions about PixelCraft services and pricing",
            "Provide detailed service information and use cases",
            "Schedule discovery calls and strategy sessions",
            "Qualify leads by understanding their needs and budget",
            "Maintain context throughout conversations",
            "Handle multi-turn interactions naturally"
        ],
        tools=[
            AgentTool(
                name="get_services_info",
                description="Get detailed information about PixelCraft's services",
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
            )
        ]
    )
    return ChatAgent(config)

class ChatAgent(BaseAgent):
    """ChatAgent for handling PixelCraft client interactions."""

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

            # Get Ollama client
            ollama = get_ollama_client()

            # Build conversation context
            context = memory.get_context_string(limit=5)
            system_prompt = self._build_system_prompt()

            # Generate response using Ollama
            response = await ollama.chat(
                model=self.config.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Extract assistant's message
            assistant_message = response["message"]["content"]

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
            await supabase.table("conversations").upsert(conversation_data).execute()
            await supabase.table("messages").insert(message_data).execute()

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
                    "model": self.config.default_model,
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
