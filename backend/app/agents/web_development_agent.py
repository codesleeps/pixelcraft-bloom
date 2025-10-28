"""Web Development Agent implementation.

This agent specializes in web development services, providing detailed
information about web development offerings, technical consultations,
and project planning for web development projects.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger("pixelcraft.agents.web_development")

# Web development service details
WEB_DEV_SERVICES = {
    "frontend_development": {
        "name": "Frontend Development",
        "technologies": ["React", "Vue.js", "Next.js", "TypeScript", "Tailwind CSS"],
        "features": ["Responsive design", "Progressive Web Apps", "Component libraries"],
        "starting_price": "$5,000"
    },
    "backend_development": {
        "name": "Backend Development",
        "technologies": ["Node.js", "Python", "FastAPI", "PostgreSQL", "MongoDB"],
        "features": ["REST APIs", "GraphQL", "Microservices", "Database design"],
        "starting_price": "$7,500"
    },
    "full_stack_development": {
        "name": "Full-Stack Development",
        "technologies": ["MERN Stack", "PERN Stack", "Django + React", "Next.js"],
        "features": ["Complete web applications", "API integration", "Deployment"],
        "starting_price": "$10,000"
    },
    "cms_development": {
        "name": "CMS Development",
        "technologies": ["WordPress", "Strapi", "Contentful", "Custom CMS"],
        "features": ["Content management", "Admin panels", "Plugin development"],
        "starting_price": "$4,000"
    },
    "ecommerce_platforms": {
        "name": "E-commerce Platforms",
        "technologies": ["Shopify", "WooCommerce", "Custom solutions"],
        "features": ["Payment integration", "Inventory management", "Order processing"],
        "starting_price": "$8,000"
    }
}

async def get_web_dev_services() -> Dict[str, Any]:
    """Tool function to retrieve web development services information."""
    return WEB_DEV_SERVICES

async def estimate_web_project(requirements: str, timeline: str, budget: str) -> Dict[str, Any]:
    """Tool function to estimate web development project costs and timeline."""
    # Simple estimation logic - in production, this would be more sophisticated
    base_costs = {
        "simple_website": 5000,
        "complex_website": 15000,
        "web_application": 25000,
        "ecommerce": 20000
    }

    # Parse requirements to determine complexity
    complexity = "simple_website"
    if "application" in requirements.lower() or "app" in requirements.lower():
        complexity = "web_application"
    elif "ecommerce" in requirements.lower() or "shop" in requirements.lower():
        complexity = "ecommerce"
    elif "complex" in requirements.lower() or "advanced" in requirements.lower():
        complexity = "complex_website"

    estimated_cost = base_costs[complexity]

    # Adjust for timeline
    timeline_multiplier = 1.0
    if "rush" in timeline.lower() or "1-2 weeks" in timeline.lower():
        timeline_multiplier = 1.5
    elif "1-3 months" in timeline.lower():
        timeline_multiplier = 1.0
    elif "3-6 months" in timeline.lower():
        timeline_multiplier = 0.8

    final_cost = estimated_cost * timeline_multiplier

    return {
        "estimated_cost": f"${final_cost:,.0f}",
        "complexity": complexity,
        "recommended_timeline": "2-4 weeks" if complexity == "simple_website" else "4-8 weeks",
        "technologies": WEB_DEV_SERVICES["full_stack_development"]["technologies"][:3]
    }

def create_web_development_agent() -> 'WebDevelopmentAgent':
    """Factory function to create a WebDevelopmentAgent instance."""
    config = BaseAgentConfig(
        agent_id="web_development",
        name="Web Development Specialist",
        description="Expert web development consultant for PixelCraft",
        default_model="llama2",
        temperature=0.3,  # Lower temperature for technical accuracy
        max_tokens=1500,
        system_prompt="""You are PixelCraft's web development specialist.
        Provide expert guidance on web development projects, technologies, and best practices.

        Focus on:
        1. Technical requirements analysis
        2. Technology stack recommendations
        3. Project complexity assessment
        4. Timeline and cost estimation
        5. Modern web development practices
        6. Performance and scalability considerations

        Always provide practical, actionable advice based on current industry standards.
        Be technical but accessible, explaining complex concepts clearly.""",
        capabilities=[
            "Web technology consulting",
            "Project planning and estimation",
            "Technology stack recommendations",
            "Performance optimization guidance",
            "Modern web development best practices",
            "Frontend and backend architecture advice"
        ],
        tools=[
            AgentTool(
                name="get_web_dev_services",
                description="Get detailed information about web development services",
                function=get_web_dev_services,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="estimate_web_project",
                description="Estimate web development project costs and timeline",
                function=estimate_web_project,
                parameters={"requirements": "str", "timeline": "str", "budget": "str"},
                required_params=["requirements"]
            )
        ]
    )
    return WebDevelopmentAgent(config)

class WebDevelopmentAgent(BaseAgent):
    """Web Development Agent for handling technical consultations."""

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a web development consultation message."""
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
                    {"role": "user", "content": f"Context: {context}\n\nUser Query: {message}"}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Extract assistant's message
            assistant_message = response["message"]["content"]

            # Add response to memory
            memory.add_message("assistant", assistant_message)

            # Persist conversation to Supabase
            try:
                supabase = get_supabase_client()
                conversation_data = {
                    "id": conversation_id,
                    "status": "active",
                    "channel": "web_dev_consultation",
                    "metadata": metadata or {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }

                await supabase.table("conversations").upsert(conversation_data).execute()
            except Exception as e:
                logger.error(f"Failed to persist conversation: {e}")

            # Log the interaction
            await self._log_interaction(
                conversation_id=conversation_id,
                action="web_dev_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )

            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "model": self.config.default_model,
                    "temperature": self.config.temperature,
                    "specialization": "web_development"
                },
                tools_used=[],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Web development consultation failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="web_dev_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise