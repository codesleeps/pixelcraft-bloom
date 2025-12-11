"""Analytics Consulting Agent implementation.

This agent specializes in analytics and data consulting services,
providing expertise in tracking setup, data analysis, and insights.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from .base import BaseAgent, BaseAgentConfig, AgentResponse, AgentTool
from ..models.manager import ModelManager
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger("agentsflowai.agents.analytics")

# Analytics service details
ANALYTICS_SERVICES = {
    "google_analytics_setup": {
        "name": "Google Analytics Setup",
        "platforms": ["Universal Analytics", "GA4"],
        "features": ["Event tracking", "E-commerce tracking", "Custom dimensions", "Goals setup"],
        "starting_price": "$1,500"
    },
    "conversion_tracking": {
        "name": "Conversion Tracking",
        "platforms": ["Google Ads", "Facebook Ads", "Custom pixels"],
        "features": ["Attribution modeling", "Multi-touch tracking", "ROI measurement", "Funnel analysis"],
        "starting_price": "$2,000"
    },
    "data_warehouse": {
        "name": "Data Warehouse Setup",
        "platforms": ["BigQuery", "Snowflake", "Custom solutions"],
        "features": ["Data pipeline", "ETL processes", "Real-time sync", "Custom dashboards"],
        "starting_price": "$5,000"
    },
    "performance_monitoring": {
        "name": "Performance Monitoring",
        "tools": ["Google Data Studio", "Tableau", "Custom dashboards"],
        "features": ["Real-time metrics", "Automated reports", "Alert systems", "Trend analysis"],
        "starting_price": "$1,200/month"
    },
    "attribution_analysis": {
        "name": "Attribution Analysis",
        "methods": ["First-touch", "Last-touch", "Multi-touch", "Algorithmic"],
        "features": ["Channel effectiveness", "Customer journey mapping", "Budget optimization", "Predictive modeling"],
        "starting_price": "$3,000"
    }
}

async def get_analytics_services() -> Dict[str, Any]:
    """Tool function to retrieve analytics services information."""
    return ANALYTICS_SERVICES

async def analyze_analytics_needs(goals: str, current_tools: str, budget: str, data_volume: str) -> Dict[str, Any]:
    """Tool function to analyze analytics setup needs."""
    # Parse budget
    try:
        monthly_budget = float(budget.replace('$', '').replace(',', '').replace('/month', ''))
    except:
        monthly_budget = 2000  # default

    # Determine analytics maturity level
    if "no analytics" in current_tools.lower() or "basic" in current_tools.lower():
        maturity = "beginner"
        priority_services = ["google_analytics_setup", "conversion_tracking"]
        timeline = "1-2 weeks"
    elif "google analytics" in current_tools.lower():
        maturity = "intermediate"
        priority_services = ["performance_monitoring", "attribution_analysis"]
        timeline = "2-4 weeks"
    else:
        maturity = "advanced"
        priority_services = ["data_warehouse", "attribution_analysis"]
        timeline = "4-8 weeks"

    # Data volume considerations
    if "high" in data_volume.lower() or "large" in data_volume.lower():
        needs_enterprise = True
        recommended_platform = "BigQuery or Snowflake"
    else:
        needs_enterprise = False
        recommended_platform = "Google Analytics 4"

    return {
        "maturity_level": maturity,
        "priority_services": priority_services,
        "recommended_platform": recommended_platform,
        "timeline": timeline,
        "estimated_cost": f"${monthly_budget * 2:,.0f}",
        "key_metrics": ["conversion_rate", "customer_acquisition_cost", "lifetime_value", "churn_rate"],
        "implementation_phases": ["Setup", "Data Collection", "Analysis", "Optimization"]
    }

def create_analytics_consulting_agent(model_manager: Optional[ModelManager] = None) -> 'AnalyticsConsultingAgent':
    """Factory function to create an AnalyticsConsultingAgent instance."""
    config = BaseAgentConfig(
        agent_id="analytics_consulting",
        name="Analytics Consulting Specialist",
        description="Data analytics expert for AgentsFlowAI",
        default_model="llama2",
        temperature=0.2,  # Very precise and technical
        max_tokens=1500,
        system_prompt="""You are AgentsFlowAI's analytics consulting specialist.
        Provide expert guidance on data analytics, tracking implementation, and performance measurement.

        Focus on:
        1. Analytics platform selection and setup
        2. Data collection and tracking implementation
        3. KPI definition and measurement
        4. Attribution modeling and analysis
        5. Data visualization and reporting
        6. Performance optimization recommendations

        Always provide data-driven insights with clear metrics and actionable recommendations.
        Explain technical concepts clearly and focus on business impact.""",
        capabilities=[
            "Analytics platform consulting",
            "Tracking implementation",
            "KPI development",
            "Data analysis and insights",
            "Attribution modeling",
            "Performance reporting"
        ],
        tools=[
            AgentTool(
                name="get_analytics_services",
                description="Get detailed information about analytics services",
                function=get_analytics_services,
                parameters={},
                required_params=[]
            ),
            AgentTool(
                name="analyze_analytics_needs",
                description="Analyze analytics setup needs based on goals and current tools",
                function=analyze_analytics_needs,
                parameters={"goals": "str", "current_tools": "str", "budget": "str", "data_volume": "str"},
                required_params=["goals", "current_tools"]
            )
        ],
        task_type="analytics_consulting",
        model_manager=model_manager
    )
    return AnalyticsConsultingAgent(config)

class AnalyticsConsultingAgent(BaseAgent):
    """Analytics Consulting Agent for data and tracking consultations."""

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process an analytics consultation message."""
        try:
            # Get or create conversation memory
            memory = self.get_memory(conversation_id)
            memory.add_message("user", message, metadata)

            # Build conversation context
            context = memory.get_context_string(limit=5)
            system_prompt = self._build_system_prompt()

            # Generate response using ModelManager (with automatic model selection and fallback)
            response = await self.model_manager.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nAnalytics Query: {message}"}
                ],
                task_type=self.config.task_type,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Extract assistant's message from ModelManager response
            assistant_message = response["message"]["content"]

            # Add response to memory
            memory.add_message("assistant", assistant_message)

            # Persist conversation to Supabase
            try:
                supabase = get_supabase_client()
                conversation_data = {
                    "id": conversation_id,
                    "status": "active",
                    "channel": "analytics_consultation",
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
                action="analytics_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={"response": assistant_message}
            )

            # Extract model metadata from ModelManager response for enhanced tracking
            model_used = response.get("model", self.config.default_model)
            model_metadata = response.get("metadata", {})

            return AgentResponse(
                content=assistant_message,
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "model": model_used,
                    "temperature": self.config.temperature,
                    "specialization": "analytics_consulting",
                    "model_performance": model_metadata  # Include latency, tokens, etc. from ModelManager
                },
                tools_used=[],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Analytics consultation failed (model error: {e})")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="analytics_consultation",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=f"Model generation failed: {str(e)}"
            )
            # ModelManager handles fallback internally, but re-raise for upstream handling
            raise
