"""Brand Design Agent implementation.
  
This agent specializes in brand design services, providing expertise
in visual identity, brand strategy, and creative design solutions.
"""
  
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
  
from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..models.manager import ModelManager
from ..utils.supabase_client import get_supabase_client
  
logger = logging.getLogger("agentsflowai.agents.brand_design")
  
# Brand design service details
BRAND_DESIGN_SERVICES = {
    "logo_design": {
        "name": "Logo Design",
        "deliverables": ["Primary logo", "Secondary versions", "Brand guidelines", "Vector files"],
        "features": ["Concept development", "Multiple iterations", "Brand alignment", "Scalable formats"],
        "starting_price": "$2,500"
    },
    "brand_identity": {
        "name": "Complete Brand Identity",
        "deliverables": ["Logo", "Color palette", "Typography", "Brand guidelines", "Business cards"],
        "features": ["Brand strategy", "Visual identity system", "Brand voice", "Implementation guide"],
        "starting_price": "$5,000"
    },
    "visual_guidelines": {
        "name": "Brand Guidelines",
        "deliverables": ["Usage guidelines", "Color specifications", "Typography rules", "Brand assets"],
        "features": ["Brand consistency", "Application examples", "Do's and don'ts", "Digital assets"],
        "starting_price": "$3,500"
    },
    "packaging_design": {
        "name": "Packaging Design",
        "deliverables": ["Package mockups", "Label design", "Brand integration", "Production files"],
        "features": ["Product photography", "Material considerations", "Brand storytelling", "Retail appeal"],
        "starting_price": "$4,000"
    },
    "marketing_materials": {
        "name": "Marketing Materials",
        "deliverables": ["Brochures", "Posters", "Social media graphics", "Email templates"],
        "features": ["Brand-consistent design", "Multi-format assets", "Print and digital", "Campaign support"],
        "starting_price": "$2,000"
    }
}
  
async def get_brand_design_services() -> Dict[str, Any]:
    """Tool function to retrieve brand design services information."""
    return BRAND_DESIGN_SERVICES
  
async def analyze_brand_needs(industry: str, target_audience: str, current_brand: str) -> Dict[str, Any]:
    """Tool function to analyze brand design needs."""
    # Industry-specific recommendations
    industry_recommendations = {
        "technology": {
            "style": "Modern, clean, innovative",
            "colors": "Blues, greens, tech-inspired palettes",
            "priority_services": ["brand_identity", "logo_design"]
        },
        "healthcare": {
            "style": "Trustworthy, professional, caring",
            "colors": "Blues, whites, calming tones",
            "priority_services": ["brand_identity", "visual_guidelines"]
        },
        "retail": {
            "style": "Engaging, approachable, memorable",
            "colors": "Vibrant, brand-specific colors",
            "priority_services": ["packaging_design", "marketing_materials"]
        },
        "professional_services": {
            "style": "Sophisticated, trustworthy, established",
            "colors": "Neutrals, accent colors for personality",
            "priority_services": ["brand_identity", "visual_guidelines"]
        }
    }
  
    industry_key = industry.lower() if industry.lower() in industry_recommendations else "professional_services"
    rec = industry_recommendations[industry_key]
  
    return {
        "recommended_style": rec["style"],
        "color_recommendations": rec["colors"],
        "priority_services": rec["priority_services"],
        "estimated_timeline": "2-4 weeks",
        "key_considerations": [
            f"Target audience: {target_audience}",
            f"Industry context: {industry}",
            f"Current brand status: {current_brand}"
        ]
    }
  
def create_brand_design_agent(model_manager: Optional[ModelManager] = None) -> 'BrandDesignAgent':
    """Factory function to create a BrandDesignAgent instance."""
    config = BaseAgentConfig(
        agent_id="brand_design",
        name="Brand Design Specialist",
        description="Creative brand design consultant for AgentsFlowAI",
        default_model="llama2",
        temperature=0.5,  # Creative but structured
        max_tokens=1500,
        system_prompt="""You are AgentsFlowAI's brand design specialist.
        Provide expert guidance on brand identity, visual design, and creative strategy.
  
        Focus on:
        1. Brand strategy and positioning
        2. Visual identity development
        3. Design system creation
        4. Brand consistency and application
        5. Industry-specific design approaches
        6. Creative concept development
  
        Always consider the target audience, industry context, and brand personality.
        Provide practical design recommendations with clear deliverables and timelines.""",
        capabilities=[
            "Brand strategy consulting",
            "Visual identity design",
            "Creative concept development",
            "Design system planning",
            "Brand guidelines creation",
            "Industry-specific design advice"
        ],
        tools=[
            AgentTool(
                name="get_brand_design_services",
                description="Get detailed information about brand design services",
                function=get_brand_design_services,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="analyze_brand_needs",
                description="Analyze brand design needs based on industry and audience",
                function=analyze_brand_needs,
                parameters={"industry": "str", "target_audience": "str", "current_brand": "str"},
                required_params=["industry", "target_audience"]
            )
        ],
        task_type="brand_design",
        model_manager=model_manager
    )
    return BrandDesignAgent(config)
  
class BrandDesignAgent(BaseAgent):
    """Brand Design Agent for creative brand consultations."""
  
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a brand design consultation message."""
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
                {"role": "user", "content": f"Context: {context}\n\nDesign Query: {message}"}
            ]
            assistant_message = await self._chat_with_model(
                messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
  
            # Add response to memory
            memory.add_message("assistant", assistant_message)
  
            # Persist conversation to Supabase
            try:
                supabase = get_supabase_client()
                conversation_data = {
                    "id": conversation_id,
                    "status": "active",
                    "channel": "brand_design_consultation",
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
                action="brand_design_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )
  
            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "temperature": self.config.temperature,
                    "specialization": "brand_design",
                    "model_selection": "managed_by_model_manager"
                },
                tools_used=[],
                model_used=None,  # Model determined by ModelManager
                timestamp=datetime.utcnow()
            )
  
        except Exception as e:
            logger.exception(f"Brand design consultation failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="brand_design_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise
