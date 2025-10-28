"""Digital Marketing Agent implementation.

This agent specializes in digital marketing services, providing expertise
in marketing strategies, campaign planning, analytics, and growth tactics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client

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

def create_digital_marketing_agent() -> 'DigitalMarketingAgent':
    """Factory function to create a DigitalMarketingAgent instance."""
    config = BaseAgentConfig(
        agent_id="digital_marketing",
        name="Digital Marketing Strategist",
        description="Expert digital marketing consultant for PixelCraft",
        default_model="llama2",
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
                    {"role": "user", "content": f"Context: {context}\n\nMarketing Query: {message}"}
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
                    "model": self.config.default_model,
                    "temperature": self.config.temperature,
                    "specialization": "digital_marketing"
                },
                tools_used=[],
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