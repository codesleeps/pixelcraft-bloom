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
from ..models.manager import ModelManager
from ..utils.supabase_client import get_supabase_client
from ..utils.external_tools import create_crm_contact, create_crm_deal, send_email, create_calendar_event

logger = logging.getLogger("agentsflowai.agents.web_development")

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

async def create_project_lead(name: str, email: str, company: str, project_requirements: str, budget: str, timeline: str) -> Dict[str, Any]:
    """Create a project lead in CRM and send confirmation email."""
    # Create CRM contact
    crm_result = await create_crm_contact(
        email=email,
        first_name=name.split()[0] if name else "",
        last_name=" ".join(name.split()[1:]) if name and len(name.split()) > 1 else "",
        company=company,
        metadata={"project_requirements": project_requirements, "budget": budget, "timeline": timeline}
    )
    
    contact_id = crm_result.get("contact_id")
    deal_id = None
    
    # If CRM contact creation succeeded, create a deal
    if contact_id and not crm_result.get("error"):
        deal_result = await create_crm_deal(
            contact_id=contact_id,
            deal_name=f"Web Development Project - {company}",
            amount=float(budget.replace("$", "").replace(",", "")) if budget else 0,
            stage="qualified_to_buy",
            metadata={"project_requirements": project_requirements, "timeline": timeline}
        )
        deal_id = deal_result.get("deal_id") if not deal_result.get("error") else None
    
    # Send confirmation email
    email_subject = "Project Inquiry Received - AgentsFlowAI Web Development"
    email_content = f"""
    Dear {name},

    Thank you for your interest in AgentsFlowAI's web development services!

    Project Summary:
    - Requirements: {project_requirements}
    - Budget: {budget}
    - Timeline: {timeline}

    Next Steps:
    1. Our team will review your requirements within 24 hours
    2. We'll schedule a technical consultation to discuss details
    3. Receive a detailed project proposal and quote

    If you have any immediate questions, please reply to this email.

    Best regards,
    AgentsFlowAI Web Development Team
    """
    
    email_result = await send_email(
        to_email=email,
        subject=email_subject,
        html_content=email_content
    )
    
    return {
        "crm_contact_id": contact_id,
        "crm_deal_id": deal_id,
        "email_status": "sent" if not email_result.get("error") else "failed",
        "crm_status": "created" if contact_id else "failed",
        "deal_status": "created" if deal_id else "skipped" if contact_id else "failed"
    }

async def schedule_technical_consultation(client_email: str, client_name: str, preferred_date: str, project_type: str) -> Dict[str, Any]:
    """Schedule a technical consultation and send calendar invite."""
    # Parse preferred_date (assume ISO format or simple date)
    # For simplicity, assume preferred_date is in YYYY-MM-DDTHH:MM:SSZ format
    start_time = preferred_date
    end_time = (datetime.fromisoformat(preferred_date.replace('Z', '+00:00')) + datetime.timedelta(minutes=60)).isoformat() + 'Z'
    
    # Create calendar event
    event_result = await create_calendar_event(
        summary=f"Technical Consultation - {project_type}",
        start_time=start_time,
        end_time=end_time,
        attendees=[client_email, "tech@agentsflowai.com"],
        description=f"Technical consultation for {project_type} project with {client_name}"
    )
    
    event_id = event_result.get("event_id")
    event_link = event_result.get("link")
    
    # Send calendar invite email
    email_subject = "Technical Consultation Scheduled - AgentsFlowAI"
    email_content = f"""
    Dear {client_name},

    Your technical consultation has been scheduled!

    Details:
    - Date & Time: {start_time}
    - Duration: 60 minutes
    - Project Type: {project_type}
    - Meeting Link: {event_link or 'To be provided'}

    Agenda:
    - Review project requirements
    - Discuss technical approach
    - Address questions and concerns
    - Next steps and timeline

    Please ensure you have a stable internet connection and any relevant project materials ready.

    Best regards,
    AgentsFlowAI Technical Team
    """
    
    email_result = await send_email(
        to_email=client_email,
        subject=email_subject,
        html_content=email_content
    )
    
    return {
        "event_id": event_id,
        "event_link": event_link,
        "email_status": "sent" if not email_result.get("error") else "failed",
        "calendar_status": "scheduled" if event_id else "failed"
    }

def create_web_development_agent(model_manager: Optional[ModelManager] = None) -> 'WebDevelopmentAgent':
    """Factory function to create a WebDevelopmentAgent instance."""
    config = BaseAgentConfig(
        agent_id="web_development",
        name="Web Development Specialist",
        description="Expert web development consultant for AgentsFlowAI",
        default_model="llama2",
        temperature=0.3,  # Lower temperature for technical accuracy
        max_tokens=1500,
        system_prompt="""You are AgentsFlowAI's web development specialist.
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
            ),
            AgentTool(
                name="create_project_lead",
                description="Create a project lead in CRM and send confirmation email",
                function=create_project_lead,
                parameters={"name": "str", "email": "str", "company": "str", "project_requirements": "str", "budget": "str", "timeline": "str"},
                required_params=["name", "email", "company", "project_requirements", "budget", "timeline"]
            ),
            AgentTool(
                name="schedule_technical_consultation",
                description="Schedule a technical consultation and send calendar invite",
                function=schedule_technical_consultation,
                parameters={"client_email": "str", "client_name": "str", "preferred_date": "str", "project_type": "str"},
                required_params=["client_email", "client_name", "preferred_date", "project_type"]
            )
        ],
        task_type="web_development",
        model_manager=model_manager
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

            # Build conversation context
            context = memory.get_context_string(limit=5)
            system_prompt = self._build_system_prompt()

            # Generate response using ModelManager
            response = await self.model_manager.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nUser Query: {message}"}
                ],
                task_type=self.config.task_type,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Extract assistant's message and model used
            assistant_message = response["message"]["content"]
            model_used = response.get("model", self.config.default_model)

            # Analyze message for tool triggers
            tools_used = []
            tool_results = {}
            tool_errors = []

            # Check for project inquiry intent (email and requirements mentioned)
            if ("email" in message.lower() or "@" in message) and ("project" in message.lower() or "website" in message.lower() or "development" in message.lower()):
                # Extract parameters from message and metadata
                name = metadata.get("name", "") if metadata else ""
                email = metadata.get("email", "") if metadata else ""
                company = metadata.get("company", "") if metadata else ""
                requirements = message  # Use full message as requirements
                budget = metadata.get("budget", "") if metadata else ""
                timeline = metadata.get("timeline", "") if metadata else ""

                if name and email and company and requirements:
                    try:
                        lead_result = await self.use_tool(conversation_id, "create_project_lead", {
                            "name": name,
                            "email": email,
                            "company": company,
                            "project_requirements": requirements,
                            "budget": budget,
                            "timeline": timeline
                        })
                        tools_used.append("create_project_lead")
                        tool_results["create_project_lead"] = lead_result
                    except Exception as e:
                        error_msg = f"Failed to create project lead: {str(e)}"
                        logger.error(error_msg)
                        tool_errors.append(error_msg)
                        assistant_message += f"\n\nNote: {error_msg}. Please contact support if needed."

            # Check for scheduling intent
            if "schedule" in message.lower() or "consultation" in message.lower() or "meeting" in message.lower():
                # Extract parameters
                client_email = metadata.get("email", "") if metadata else ""
                client_name = metadata.get("name", "") if metadata else ""
                preferred_date = metadata.get("preferred_date", "") if metadata else ""
                project_type = metadata.get("project_type", "web development") if metadata else "web development"

                if client_email and client_name and preferred_date:
                    try:
                        schedule_result = await self.use_tool(conversation_id, "schedule_technical_consultation", {
                            "client_email": client_email,
                            "client_name": client_name,
                            "preferred_date": preferred_date,
                            "project_type": project_type
                        })
                        tools_used.append("schedule_technical_consultation")
                        tool_results["schedule_technical_consultation"] = schedule_result
                    except Exception as e:
                        error_msg = f"Failed to schedule consultation: {str(e)}"
                        logger.error(error_msg)
                        tool_errors.append(error_msg)
                        assistant_message += f"\n\nNote: {error_msg}. Please try again or contact support."

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
                output_data={"response": assistant_message, "tool_results": tool_results, "tool_errors": tool_errors}
            )

            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "model": model_used,
                    "temperature": self.config.temperature,
                    "specialization": "web_development",
                    "tool_results": tool_results,
                    "tool_errors": tool_errors
                },
                tools_used=tools_used,
                model_used=model_used,
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