"""Content Creation Agent implementation.

This agent specializes in content creation services, providing expertise
in content strategy, copywriting, and multi-channel content production.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..models.manager import ModelManager
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger("pixelcraft.agents.content_creation")

# Content creation service details
CONTENT_SERVICES = {
    "blog_writing": {
        "name": "Blog Writing",
        "types": ["SEO articles", "Thought leadership", "How-to guides", "Industry insights"],
        "features": ["Keyword research", "SEO optimization", "Engaging headlines", "Call-to-action"],
        "starting_price": "$500/article"
    },
    "social_media_content": {
        "name": "Social Media Content",
        "platforms": ["Instagram", "LinkedIn", "Twitter", "Facebook", "TikTok"],
        "features": ["Platform-specific copy", "Hashtags", "Visual concepts", "Posting schedule"],
        "starting_price": "$800/month"
    },
    "email_marketing": {
        "name": "Email Marketing Copy",
        "types": ["Newsletters", "Promotional emails", "Welcome sequences", "Automated campaigns"],
        "features": ["Subject lines", "Personalization", "A/B testing", "Conversion focus"],
        "starting_price": "$300/email"
    },
    "video_scripts": {
        "name": "Video Scripts & Storytelling",
        "types": ["Product videos", "Brand stories", "Tutorial videos", "Social media videos"],
        "features": ["Story structure", "Engaging hooks", "Clear messaging", "Call-to-action"],
        "starting_price": "$400/script"
    },
    "website_copy": {
        "name": "Website Copy",
        "types": ["Homepage", "About pages", "Service pages", "Landing pages"],
        "features": ["SEO-friendly", "Conversion-focused", "Brand voice", "User experience"],
        "starting_price": "$1,200/page"
    }
}

async def get_content_services() -> Dict[str, Any]:
    """Tool function to retrieve content creation services information."""
    return CONTENT_SERVICES

async def plan_content_strategy(goals: str, audience: str, channels: str, budget: str) -> Dict[str, Any]:
    """Tool function to plan content marketing strategy."""
    # Parse budget
    try:
        monthly_budget = float(budget.replace('$', '').replace(',', '').replace('/month', ''))
    except:
        monthly_budget = 2000  # default

    # Content mix based on goals
    content_mix = {}
    if "brand_awareness" in goals.lower():
        content_mix = {"social_media": 40, "blog": 30, "video": 20, "email": 10}
    elif "lead_generation" in goals.lower():
        content_mix = {"blog": 40, "email": 30, "social_media": 20, "website": 10}
    elif "sales" in goals.lower():
        content_mix = {"email": 40, "website": 30, "social_media": 20, "video": 10}
    else:
        content_mix = {"blog": 30, "social_media": 30, "email": 25, "video": 15}

    # Calculate content volume based on budget
    content_volume = {
        "blog_posts": max(2, int(monthly_budget / 500)),
        "social_posts": max(12, int(monthly_budget / 200)),
        "emails": max(4, int(monthly_budget / 300)),
        "videos": max(1, int(monthly_budget / 800))
    }

    return {
        "content_mix": content_mix,
        "monthly_volume": content_volume,
        "recommended_channels": channels.split(',') if channels else ["blog", "social_media"],
        "content_pillars": ["industry_expertise", "customer_success", "product_education"],
        "estimated_roi": f"${monthly_budget * 3:,.0f}",
        "key_metrics": ["engagement_rate", "conversion_rate", "lead_quality", "brand_sentiment"]
    }

def create_content_creation_agent(model_manager: Optional[ModelManager] = None) -> 'ContentCreationAgent':
    """Factory function to create a ContentCreationAgent instance."""
    config = BaseAgentConfig(
        agent_id="content_creation",
        name="Content Creation Specialist",
        description="Creative content strategist for PixelCraft",
        default_model="llama2",
        temperature=0.6,  # Creative but focused
        max_tokens=1500,
        system_prompt="""You are PixelCraft's content creation specialist.
        Provide expert guidance on content strategy, copywriting, and multi-channel content production.

        Focus on:
        1. Content strategy development
        2. Audience analysis and targeting
        3. Channel-specific content optimization
        4. Brand voice and messaging
        5. SEO and discoverability
        6. Performance measurement and optimization

        Always create engaging, conversion-focused content that resonates with the target audience.
        Provide practical content recommendations with clear deliverables and timelines.""",
        capabilities=[
            "Content strategy planning",
            "Copywriting and messaging",
            "Multi-channel content creation",
            "SEO content optimization",
            "Brand voice development",
            "Content performance analysis"
        ],
        tools=[
            AgentTool(
                name="get_content_services",
                description="Get detailed information about content creation services",
                function=get_content_services,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="plan_content_strategy",
                description="Plan content marketing strategy based on goals and budget",
                function=plan_content_strategy,
                parameters={"goals": "str", "audience": "str", "channels": "str", "budget": "str"},
                required_params=["goals", "audience"]
            )
        ],
        task_type="content_creation",
        model_manager=model_manager
    )
    return ContentCreationAgent(config)

class ContentCreationAgent(BaseAgent):
    """Content Creation Agent for content strategy consultations."""

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a content creation consultation message."""
        if not self.model_manager:
            raise ValueError("ModelManager not configured for ContentCreationAgent")

        try:
            # Get or create conversation memory
            memory = self.get_memory(conversation_id)
            memory.add_message("user", message, metadata)

            # Build conversation context
            context = memory.get_context_string(limit=5)
            system_prompt = self._build_system_prompt()

            # Generate response using ModelManager
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nContent Query: {message}"}
            ]
            response = await self.model_manager.chat(
                messages,
                self.config.task_type,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Extract assistant's message and model used
            assistant_message = response["message"]["content"]
            model_used = response.get("model_used")

            # Add response to memory
            memory.add_message("assistant", assistant_message)

            # Persist conversation to Supabase
            try:
                supabase = get_supabase_client()
                conversation_data = {
                    "id": conversation_id,
                    "status": "active",
                    "channel": "content_creation_consultation",
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
                action="content_creation_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )

            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "temperature": self.config.temperature,
                    "specialization": "content_creation"
                },
                tools_used=[],
                model_used=model_used,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Content creation consultation failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="content_creation_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise
