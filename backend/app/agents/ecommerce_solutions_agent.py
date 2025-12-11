"""E-commerce Solutions Agent implementation.

This agent specializes in e-commerce solutions, providing expertise
in online store development, payment integration, and sales optimization.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..utils.supabase_client import get_supabase_client
from ..models.manager import ModelManager

logger = logging.getLogger("agentsflowai.agents.ecommerce")

# E-commerce service details
ECOMMERCE_SERVICES = {
    "shopify_stores": {
        "name": "Shopify Store Development",
        "platform": "Shopify",
        "features": ["Custom themes", "App integrations", "Payment setup", "Inventory management"],
        "starting_price": "$5,000"
    },
    "woocommerce_stores": {
        "name": "WooCommerce Development",
        "platform": "WordPress + WooCommerce",
        "features": ["Custom plugins", "Theme development", "Payment gateways", "Shipping integration"],
        "starting_price": "$6,000"
    },
    "custom_ecommerce": {
        "name": "Custom E-commerce Platform",
        "platform": "Custom built",
        "features": ["Full-stack development", "Scalable architecture", "Advanced features", "API integrations"],
        "starting_price": "$15,000"
    },
    "marketplace_platforms": {
        "name": "Marketplace Development",
        "platform": "Multi-vendor",
        "features": ["Vendor management", "Commission system", "Product catalog", "Order management"],
        "starting_price": "$25,000"
    },
    "ecommerce_optimization": {
        "name": "E-commerce Optimization",
        "platform": "Existing stores",
        "features": ["Performance optimization", "Conversion rate improvement", "Mobile optimization", "Analytics setup"],
        "starting_price": "$3,500"
    }
}

async def get_ecommerce_services() -> Dict[str, Any]:
    """Tool function to retrieve e-commerce services information."""
    return ECOMMERCE_SERVICES

async def estimate_ecommerce_project(products: str, monthly_sales: str, features: str) -> Dict[str, Any]:
    """Tool function to estimate e-commerce project requirements."""
    # Parse inputs
    try:
        num_products = int(products.replace(',', ''))
        monthly_rev = float(monthly_sales.replace('$', '').replace(',', '').replace('/month', ''))
    except:
        num_products = 50  # default
        monthly_rev = 5000  # default

    # Determine complexity based on scale
    if num_products < 50 and monthly_rev < 10000:
        complexity = "small_store"
        platform = "Shopify"
        estimated_cost = 5000
        timeline = "2-3 weeks"
    elif num_products < 500 and monthly_rev < 50000:
        complexity = "medium_store"
        platform = "Shopify or WooCommerce"
        estimated_cost = 8000
        timeline = "3-4 weeks"
    elif num_products < 1000 and monthly_rev < 100000:
        complexity = "large_store"
        platform = "Custom or WooCommerce"
        estimated_cost = 15000
        timeline = "6-8 weeks"
    else:
        complexity = "enterprise"
        platform = "Custom platform"
        estimated_cost = 30000
        timeline = "3-6 months"

    return {
        "recommended_platform": platform,
        "estimated_cost": f"${estimated_cost:,.0f}",
        "timeline": timeline,
        "complexity": complexity,
        "key_features": ["Payment processing", "Inventory management", "Shipping integration", "Customer accounts"],
        "monthly_maintenance": f"${estimated_cost * 0.1:,.0f}"
    }

def create_ecommerce_solutions_agent(model_manager: Optional[ModelManager] = None) -> 'EcommerceSolutionsAgent':
    """Factory function to create an EcommerceSolutionsAgent instance."""
    config = BaseAgentConfig(
        agent_id="ecommerce_solutions",
        name="E-commerce Solutions Specialist",
        description="Expert e-commerce consultant for AgentsFlowAI",
        temperature=0.3,  # Technical and precise
        max_tokens=1500,
        system_prompt="""You are AgentsFlowAI's e-commerce solutions specialist.
        Provide expert guidance on online store development, platform selection, and sales optimization.

        Focus on:
        1. Platform recommendations (Shopify, WooCommerce, custom)
        2. Technical architecture and scalability
        3. Payment and shipping integrations
        4. User experience and conversion optimization
        5. Inventory and order management systems
        6. E-commerce analytics and reporting

        Always consider business scale, technical requirements, and growth potential.
        Provide practical recommendations with clear cost-benefit analysis.""",
        capabilities=[
            "E-commerce platform consulting",
            "Technical architecture planning",
            "Payment integration guidance",
            "Conversion optimization",
            "Scalability planning",
            "Analytics and reporting setup"
        ],
        tools=[
            AgentTool(
                name="get_ecommerce_services",
                description="Get detailed information about e-commerce services",
                function=get_ecommerce_services,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="estimate_ecommerce_project",
                description="Estimate e-commerce project requirements and costs",
                function=estimate_ecommerce_project,
                parameters={"products": "str", "monthly_sales": "str", "features": "str"},
                required_params=["products", "monthly_sales"]
            )
        ],
        task_type="ecommerce_solutions",
        model_manager=model_manager
    )
    return EcommerceSolutionsAgent(config)

class EcommerceSolutionsAgent(BaseAgent):
    """E-commerce Solutions Agent for online store consultations."""

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process an e-commerce consultation message."""
        try:
            # Get or create conversation memory
            memory = self.get_memory(conversation_id)
            memory.add_message("user", message, metadata)

            # Build conversation context
            context = memory.get_context_string(limit=5)
            system_prompt = self._build_system_prompt()

            # Generate response using ModelManager with automatic model selection and fallback
            try:
                assistant_message = await self._chat_with_model(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context: {context}\n\nE-commerce Query: {message}"}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                model_used = None  # Model info not available from helper
            except Exception as e:
                logger.error(f"Model call failed for task_type '{self.config.task_type}': {e}")
                raise

            # Add response to memory
            memory.add_message("assistant", assistant_message)

            # Persist conversation to Supabase
            try:
                supabase = get_supabase_client()
                conversation_data = {
                    "id": conversation_id,
                    "status": "active",
                    "channel": "ecommerce_consultation",
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
                action="ecommerce_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )

            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "temperature": self.config.temperature,
                    "specialization": "ecommerce_solutions"
                },
                tools_used=[],
                model_used=model_used,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"E-commerce consultation failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="ecommerce_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise
