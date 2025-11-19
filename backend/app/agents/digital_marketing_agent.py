"""Digital Marketing Agent implementation.

This agent specializes in digital marketing services, providing expertise
in marketing strategies, campaign planning, analytics, and growth tactics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..utils.supabase_client import get_supabase_client
from ..utils.external_tools import create_crm_contact, create_crm_deal, send_email, send_template_email, create_calendar_event

logger = logging.getLogger("pixelcraft.agents.digital_marketing")

# Digital marketing service details
DIGITAL_MARKETING_SERVICES = {
    "seo_optimization": {
        "name": "SEO Optimization",
        "strategies": ["Technical SEO", "Content SEO", "Local SEO", "E-commerce SEO"],
        "features": ["Keyword research", "On-page optimization", "Link building", "Performance tracking"],
        "starting_price": "$2,000/month"
    },
    "content_marketing": {
        "name": "Content Marketing",
        "strategies": ["Blog content", "Social media content", "Video marketing", "Email campaigns"],
        "features": ["Content strategy", "Content creation", "Distribution planning", "Performance analysis"],
        "starting_price": "$1,800/month"
    },
    "social_media_management": {
        "name": "Social Media Management",
        "platforms": ["Facebook", "Instagram", "LinkedIn", "Twitter", "TikTok"],
        "features": ["Content creation", "Community management", "Ad campaigns", "Analytics reporting"],
        "starting_price": "$1,500/month"
    },
    "paid_advertising": {
        "name": "Paid Advertising",
        "platforms": ["Google Ads", "Facebook Ads", "LinkedIn Ads", "Display networks"],
        "features": ["Campaign setup", "Audience targeting", "Creative optimization", "ROI tracking"],
        "starting_price": "$2,500/month"
    },
    "email_marketing": {
        "name": "Email Marketing",
        "tools": ["Mailchimp", "Klavi", "Sendinblue", "Custom solutions"],
        "features": ["List building", "Campaign automation", "A/B testing", "Performance analytics"],
        "starting_price": "$1,200/month"
    }
}

async def get_digital_marketing_services() -> Dict[str, Any]:
    """Tool function to retrieve digital marketing services information."""
    return DIGITAL_MARKETING_SERVICES

async def analyze_marketing_roi(budget: str, goals: str, industry: str) -> Dict[str, Any]:
    """Tool function to analyze potential marketing ROI."""
    # Parse budget
    budget_num = float(budget.replace('$', '').replace(',', '').replace('/month', ''))

    # Industry multipliers (rough estimates)
    industry_multipliers = {
        "ecommerce": 1.5,
        "saas": 1.3,
        "professional_services": 1.0,
        "retail": 1.2,
        "healthcare": 0.8
    }

    multiplier = industry_multipliers.get(industry.lower(), 1.0)

    # Calculate potential ROI
    base_roi = budget_num * 3 * multiplier  # Rough 3x return
    conservative_roi = budget_num * 2 * multiplier
    aggressive_roi = budget_num * 5 * multiplier

    return {
        "conservative_roi": f"${conservative_roi:,.0f}",
        "expected_roi": f"${base_roi:,.0f}",
        "optimistic_roi": f"${aggressive_roi:,.0f}",
        "payback_period": "3-6 months",
        "recommended_budget_allocation": {
            "SEO": "30%",
            "Content Marketing": "25%",
            "Paid Advertising": "30%",
            "Social Media": "15%"
        }
    }

async def create_marketing_lead(name: str, email: str, company: str, marketing_goals: str, budget: str, channels: List[str]) -> Dict[str, Any]:
    # Split name into first and last
    name_parts = name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Create CRM contact
    contact_result = await create_crm_contact(
        email=email,
        first_name=first_name,
        last_name=last_name,
        company=company,
        metadata={
            "marketing_goals": marketing_goals,
            "budget": budget,
            "preferred_channels": ', '.join(channels)
        }
    )
    
    if contact_result.get("error"):
        return {"error": "Failed to create CRM contact", "details": contact_result}
    
    contact_id = contact_result.get("contact_id")
    deal_result = None
    if contact_id:
        # Create deal
        deal_result = await create_crm_deal(
            contact_id=contact_id,
            deal_name=f"Marketing Services - {company}",
            amount=float(budget.replace('$', '').replace(',', '').replace('/month', '')),
            stage="Qualified Lead",
            metadata={"marketing_goals": marketing_goals, "channels": channels}
        )
    
    # Send welcome email
    email_result = await send_template_email(
        to_email=email,
        template_id="marketing_welcome_template",  # Assuming a template ID
        template_data={
            "name": name,
            "company": company,
            "marketing_goals": marketing_goals,
            "budget": budget,
            "channels": channels
        }
    )
    
    return {
        "contact_id": contact_id,
        "deal_id": deal_result.get("deal_id") if deal_result and not deal_result.get("error") else None,
        "email_status": email_result
    }

async def send_marketing_proposal(client_email: str, client_name: str, recommended_services: List[str], estimated_budget: str, roi_projection: Dict[str, Any]) -> Dict[str, Any]:
    # Build HTML content
    services_html = "<ul>" + "".join(f"<li>{service}</li>" for service in recommended_services) + "</ul>"
    roi_html = f"<p>Conservative ROI: {roi_projection.get('conservative_roi', 'N/A')}</p><p>Expected ROI: {roi_projection.get('expected_roi', 'N/A')}</p><p>Optimistic ROI: {roi_projection.get('optimistic_roi', 'N/A')}</p>"
    
    html_content = f"""
    <h2>Personalized Marketing Proposal for {client_name}</h2>
    <p>Dear {client_name},</p>
    <p>Based on our analysis, we recommend the following services:</p>
    {services_html}
    <p>Estimated Budget: {estimated_budget}</p>
    <h3>ROI Projections:</h3>
    {roi_html}
    <p>Please find attached our detailed proposal PDF.</p>
    <p>Best regards,<br>PixelCraft Digital Marketing Team</p>
    """
    
    # Send email
    result = await send_email(
        to_email=client_email,
        subject=f"Marketing Proposal for {client_name}",
        html_content=html_content
    )
    
    return result

async def schedule_strategy_session(client_email: str, client_name: str, preferred_date: str, focus_areas: List[str]) -> Dict[str, Any]:
    # Schedule event
    event_result = await create_calendar_event(
        summary=f"Marketing Strategy Session - {client_name}",
        start_time=preferred_date,  # Assuming preferred_date is in ISO format
        end_time=(datetime.fromisoformat(preferred_date.replace('Z', '+00:00')) + datetime.timedelta(minutes=90)).isoformat(),
        attendees=[client_email, "marketing@pixelcraft.com"],
        description=f"Focus areas: {', '.join(focus_areas)}. Pre-session questionnaire will be sent separately."
    )
    
    if event_result.get("error"):
        return {"error": "Failed to schedule event", "details": event_result}
    
    # Send confirmation email
    confirmation_html = f"""
    <h2>Marketing Strategy Session Confirmed</h2>
    <p>Dear {client_name},</p>
    <p>Your marketing strategy session has been scheduled.</p>
    <p>Date & Time: {preferred_date}</p>
    <p>Meeting Link: {event_result.get('link', 'TBD')}</p>
    <p>Focus Areas: {', '.join(focus_areas)}</p>
    <p>Please complete the pre-session questionnaire attached.</p>
    <p>Best regards,<br>PixelCraft Team</p>
    """
    
    email_result = await send_email(
        to_email=client_email,
        subject="Marketing Strategy Session Confirmation",
        html_content=confirmation_html
    )
    
    return {
        "event_id": event_result.get("event_id"),
        "meeting_link": event_result.get("link"),
        "email_status": email_result
    }

def create_digital_marketing_agent() -> 'DigitalMarketingAgent':
    """Factory function to create a DigitalMarketingAgent instance."""
    config = BaseAgentConfig(
        agent_id="digital_marketing",
        name="Digital Marketing Strategist",
        description="Expert digital marketing consultant for PixelCraft",
        temperature=0.4,  # Balanced for strategic thinking
        max_tokens=1500,
        system_prompt="""You are PixelCraft's digital marketing strategist.
        Provide expert guidance on digital marketing strategies, campaign planning, and growth tactics.

        Focus on:
        1. Marketing strategy development
        2. Channel selection and optimization
        3. Budget allocation and ROI analysis
        4. Performance measurement and analytics
        5. Industry-specific marketing approaches
        6. Conversion rate optimization

        Always provide data-driven recommendations with clear metrics and KPIs.
        Consider both short-term results and long-term brand building.""",
        capabilities=[
            "Marketing strategy consulting",
            "Campaign planning and execution",
            "ROI analysis and forecasting",
            "Channel optimization",
            "Performance analytics",
            "Conversion optimization"
        ],
        task_type="digital_marketing",
        tools=[
            AgentTool(
                name="get_digital_marketing_services",
                description="Get detailed information about digital marketing services",
                function=get_digital_marketing_services,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="analyze_marketing_roi",
                description="Analyze potential marketing ROI based on budget and goals",
                function=analyze_marketing_roi,
                parameters={"budget": "str", "goals": "str", "industry": "str"},
                required_params=["budget", "goals"]
            ),
            AgentTool(
                name="create_marketing_lead",
                description="Create a marketing lead in CRM and send welcome email",
                function=create_marketing_lead,
                parameters={"name": "str", "email": "str", "company": "str", "marketing_goals": "str", "budget": "str", "channels": "List[str]"},
                required_params=["name", "email", "company", "marketing_goals", "budget", "channels"]
            ),
            AgentTool(
                name="send_marketing_proposal",
                description="Send a personalized marketing proposal via email",
                function=send_marketing_proposal,
                parameters={"client_email": "str", "client_name": "str", "recommended_services": "List[str]", "estimated_budget": "str", "roi_projection": "Dict[str, Any]"},
                required_params=["client_email", "client_name", "recommended_services", "estimated_budget", "roi_projection"]
            ),
            AgentTool(
                name="schedule_strategy_session",
                description="Schedule a marketing strategy session and send confirmation",
                function=schedule_strategy_session,
                parameters={"client_email": "str", "client_name": "str", "preferred_date": "str", "focus_areas": "List[str]"},
                required_params=["client_email", "client_name", "preferred_date", "focus_areas"]
            )
        ]
    )
    return DigitalMarketingAgent(config)

class DigitalMarketingAgent(BaseAgent):
    """Digital Marketing Agent for marketing strategy consultations."""

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a digital marketing consultation message."""
        try:
            # Get or create conversation memory
            memory = self.get_memory(conversation_id)
            memory.add_message("user", message, metadata)

            # Build conversation context
            context = memory.get_context_string(limit=5)
            system_prompt = self._build_system_prompt()

            # Generate response using ModelManager with automatic model selection and fallback
            try:
                response = await self.model_manager.chat(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context: {context}\n\nMarketing Query: {message}"}
                    ],
                    task_type=self.config.task_type,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                # Extract assistant's message
                assistant_message = response["message"]["content"]
                model_used = response.get("model_used")
            except Exception as e:
                logger.error(f"ModelManager chat failed, falling back to error response: {e}")
                assistant_message = "I'm sorry, I'm experiencing technical difficulties with my AI models right now. Please try again later or contact support."
                model_used = None

            # Analyze conversation for tool usage
            tools_used = []
            tool_results = {}
            
            # Check for marketing inquiry
            if "inquiry" in message.lower() or "interested" in message.lower() or "budget" in message.lower():
                # Extract params from context/metadata
                name = metadata.get("name", "Unknown") if metadata else "Unknown"
                email = metadata.get("email", "") if metadata else ""
                company = metadata.get("company", "") if metadata else ""
                goals = metadata.get("goals", "") if metadata else ""
                budget = metadata.get("budget", "") if metadata else ""
                channels = metadata.get("channels", []) if metadata else []
                if email and name:
                    lead_result = await self.use_tool(conversation_id, "create_marketing_lead", {
                        "name": name, "email": email, "company": company, "marketing_goals": goals, "budget": budget, "channels": channels
                    })
                    tools_used.append("create_marketing_lead")
                    tool_results["create_marketing_lead"] = lead_result
            
            # Check for proposal request
            if "proposal" in message.lower() or "quote" in message.lower():
                client_name = metadata.get("name", "Client") if metadata else "Client"
                client_email = metadata.get("email", "") if metadata else ""
                services = metadata.get("recommended_services", []) if metadata else []
                budget = metadata.get("budget", "") if metadata else ""
                roi = await self.use_tool(conversation_id, "analyze_marketing_roi", {"budget": budget, "goals": "growth", "industry": "general"})
                if client_email and services:
                    proposal_result = await self.use_tool(conversation_id, "send_marketing_proposal", {
                        "client_email": client_email, "client_name": client_name, "recommended_services": services, "estimated_budget": budget, "roi_projection": roi
                    })
                    tools_used.append("send_marketing_proposal")
                    tool_results["send_marketing_proposal"] = proposal_result
            
            # Check for scheduling
            if "schedule" in message.lower() or "meeting" in message.lower() or "session" in message.lower():
                client_name = metadata.get("name", "Client") if metadata else "Client"
                client_email = metadata.get("email", "") if metadata else ""
                preferred_date = metadata.get("preferred_date", "") if metadata else ""
                focus_areas = metadata.get("focus_areas", []) if metadata else []
                if client_email and preferred_date:
                    schedule_result = await self.use_tool(conversation_id, "schedule_strategy_session", {
                        "client_email": client_email, "client_name": client_name, "preferred_date": preferred_date, "focus_areas": focus_areas
                    })
                    tools_used.append("schedule_strategy_session")
                    tool_results["schedule_strategy_session"] = schedule_result

            # Add response to memory
            memory.add_message("assistant", assistant_message)

            # Persist conversation to Supabase
            try:
                supabase = get_supabase_client()
                conversation_data = {
                    "id": conversation_id,
                    "status": "active",
                    "channel": "digital_marketing_consultation",
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
                action="digital_marketing_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )

            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "model": model_used,
                    "temperature": self.config.temperature,
                    "specialization": "digital_marketing",
                    "tool_results": tool_results
                },
                tools_used=tools_used,
                model_used=model_used,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Digital marketing consultation failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="digital_marketing_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise
