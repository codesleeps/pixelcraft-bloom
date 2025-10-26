"""Service recommendation agent.

This agent analyzes user needs and conversation context to provide personalized
service recommendations, using both keyword matching and AI analysis.
"""

from typing import Any, Dict, List, Optional
import re
import json
from datetime import datetime
import uuid
import logging
from collections import defaultdict

from .base import BaseAgent, BaseAgentConfig, AgentResponse
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger("pixelcraft.agents.recommendation")

# Mapping services to relevant keywords for matching
SERVICE_KEYWORDS = {
    "web_development": [
        "website", "web", "development", "app", "application", "mobile",
        "responsive", "cms", "wordpress", "react", "vue", "javascript",
        "frontend", "backend", "full-stack", "hosting", "deployment"
    ],
    "digital_marketing": [
        "marketing", "digital", "strategy", "campaign", "email", "automation",
        "funnel", "leads", "conversion", "advertising", "ppc", "ads",
        "customer acquisition", "growth", "roi", "analytics"
    ],
    "brand_design": [
        "brand", "design", "logo", "visual", "identity", "branding",
        "creative", "graphics", "illustration", "style guide", "colors",
        "typography", "packaging", "print", "marketing materials"
    ],
    "ecommerce_solutions": [
        "ecommerce", "shop", "store", "online store", "shopping cart",
        "products", "inventory", "payment", "shipping", "orders",
        "shopify", "woocommerce", "sales", "checkout", "marketplace"
    ],
    "content_creation": [
        "content", "writing", "blog", "article", "copywriting", "social media",
        "video", "production", "photography", "storytelling", "newsletter",
        "messaging", "posts", "editorial", "content strategy"
    ],
    "analytics_consulting": [
        "analytics", "data", "tracking", "metrics", "kpi", "reporting",
        "insights", "conversion", "google analytics", "performance",
        "measurement", "optimization", "attribution", "dashboard"
    ]
}

def create_recommendation_agent() -> 'ServiceRecommendationAgent':
    """Factory function to create a ServiceRecommendationAgent instance."""
    config = BaseAgentConfig(
        agent_id="service_recommendation",
        name="Service Recommendation Specialist",
        description="Expert system for recommending PixelCraft services",
        default_model="llama2",
        temperature=0.4,  # Moderate temperature for balanced recommendations
        max_tokens=2000,
        system_prompt="""You are PixelCraft's service recommendation specialist.
        Analyze client needs, goals, and constraints to recommend the most suitable services.
        Consider factors like:
        1. Business goals and challenges
        2. Budget constraints
        3. Timeline requirements
        4. Technical requirements
        5. Industry context
        6. Potential ROI and impact
        
        Provide recommendations in JSON format with array of recommendations, each containing:
        {
            "service": string (service identifier),
            "confidence": number (0-100),
            "reasoning": string (clear explanation),
            "priority": string (high/medium/low),
            "estimated_impact": string (description of expected outcomes),
            "suggested_approach": string (implementation strategy)
        }
        
        Focus on practical, achievable solutions that align with client needs and constraints.
        Prioritize recommendations based on potential impact and urgency.""",
        capabilities=[
            "Service matching based on needs",
            "Budget-aware recommendations",
            "Priority assessment",
            "Implementation planning",
            "Impact estimation",
            "Integration planning"
        ]
    )
    return ServiceRecommendationAgent(config)


class ServiceRecommendationAgent(BaseAgent):
    """Agent for providing personalized service recommendations."""

    def _extract_needs_and_constraints(self, text: str) -> Dict[str, Any]:
        """Extract key information from user input."""
        # Simple extraction of common patterns
        needs = {
            "budget": re.search(r'budget.*?[\$£]?\s*(\d+[k,]?\d*)', text, re.I),
            "timeline": re.search(r'timeline.*?(\d+)\s*(day|week|month)', text, re.I),
            "goals": re.findall(r'(want|need|looking for|interested in)\s+([^,.;]+)', text, re.I),
            "industry": re.search(r'(industry|sector|field).*?(\w+)', text, re.I)
        }

        return {
            "budget": needs["budget"].group(1) if needs["budget"] else None,
            "timeline": needs["timeline"].group(0) if needs["timeline"] else None,
            "goals": [g[1] for g in needs["goals"]],
            "industry": needs["industry"].group(2) if needs["industry"] else None
        }

    def _keyword_matching_score(self, text: str) -> Dict[str, float]:
        """Calculate service scores based on keyword matching."""
        text = text.lower()
        scores = defaultdict(float)
        
        # Count keyword matches for each service
        for service, keywords in SERVICE_KEYWORDS.items():
            matches = 0
            for keyword in keywords:
                matches += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            
            # Normalize score (0-100)
            max_possible_matches = len(keywords)
            scores[service] = min(100, (matches / max_possible_matches) * 100)
            
        return dict(scores)

    def _get_fallback_recommendations(self, keyword_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate fallback recommendations based on keyword matching."""
        recommendations = []
        
        for service, score in keyword_scores.items():
            if score > 20:  # Only include services with meaningful matches
                recommendations.append({
                    "service": service,
                    "confidence": score,
                    "reasoning": f"Based on keyword relevance to client needs",
                    "priority": "high" if score > 70 else "medium" if score > 40 else "low",
                    "estimated_impact": "Potential positive impact on business goals",
                    "suggested_approach": "Standard service implementation"
                })
        
        # Sort by confidence score
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:3]  # Return top 3 recommendations

    async def process_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Process a message and generate service recommendations."""
        try:
            # Extract needs and constraints
            needs = self._extract_needs_and_constraints(message)
            
            # Calculate keyword matching scores
            keyword_scores = self._keyword_matching_score(message)
            
            # Get AI recommendations
            try:
                ollama = get_ollama_client()
                response = await ollama.chat(
                    model=self.config.default_model,
                    messages=[
                        {"role": "system", "content": self.config.system_prompt},
                        {"role": "user", "content": f"Analyze needs and recommend services:\nMessage: {message}\nExtracted needs: {json.dumps(needs)}"}
                    ],
                    temperature=self.config.temperature
                )
                
                # Extract JSON from response
                content = response["message"]["content"]
                json_match = re.search(r'```json\n(.*)\n```', content, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group(1))
                else:
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        recommendations = json.loads(json_match.group(0))["recommendations"]
                    else:
                        raise ValueError("No valid JSON found in response")
                
            except Exception as e:
                logger.error(f"AI recommendation failed: {e}")
                recommendations = self._get_fallback_recommendations(keyword_scores)

            # Persist recommendations to Supabase
            try:
                supabase = get_supabase_client()
                lead_id = metadata.get("lead_id") if metadata else None
                
                for rec in recommendations:
                    recommendation_data = {
                        "id": str(uuid.uuid4()),
                        "lead_id": lead_id,
                        "conversation_id": conversation_id,
                        "service_name": rec["service"],
                        "confidence_score": rec["confidence"],
                        "reasoning": rec["reasoning"],
                        "priority": rec["priority"],
                        "status": "suggested",
                        "metadata": {
                            "estimated_impact": rec["estimated_impact"],
                            "suggested_approach": rec["suggested_approach"],
                            "keyword_score": keyword_scores.get(rec["service"], 0)
                        },
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    await supabase.table("service_recommendations").insert(recommendation_data).execute()
                    
            except Exception as e:
                logger.error(f"Failed to persist recommendations: {e}")

            # Log the interaction
            await self._log_interaction(
                conversation_id=conversation_id,
                action="recommend_services",
                input_data={
                    "message": message,
                    "needs": needs,
                    "keyword_scores": keyword_scores
                },
                output_data={"recommendations": recommendations}
            )

            return AgentResponse(
                content=json.dumps(recommendations, indent=2),
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata={
                    "needs": needs,
                    "keyword_scores": keyword_scores,
                    "recommendations": recommendations
                },
                tools_used=[],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Service recommendation failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="recommend_services",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise