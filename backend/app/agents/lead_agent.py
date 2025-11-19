from typing import Any, Dict, List, Optional
import json
import re
import logging
from datetime import datetime

from .base import BaseAgent, BaseAgentConfig, AgentResponse
from ..utils.supabase_client import get_supabase_client
from .orchestrator import orchestrator

logger = logging.getLogger("pixelcraft.agents.lead")

# Scoring weights for different attributes
SCORE_WEIGHTS = {
    "budget": 30,  # Budget range appropriate for services
    "timeline": 15,  # Clear project timeline
    "company": 10,  # Has company information
    "message": 10,  # Detailed inquiry message
    "services": 5,  # Clear service interests
}

# Budget ranges and their scores
BUDGET_SCORES = {
    "0-1000": 0,
    "1000-5000": 10,
    "5000-10000": 20,
    "10000-25000": 25,
    "25000+": 30,
}

# Timeline scores
TIMELINE_SCORES = {
    "immediate": 15,
    "1-3_months": 15,
    "3-6_months": 10,
    "6-12_months": 5,
    "unknown": 0,
}

class LeadQualificationAgent(BaseAgent):
    """Agent for qualifying and scoring leads based on available information."""

    def _calculate_heuristic_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate initial heuristic score based on available lead data."""
        score = 0
        reasons = []

        # Budget score
        budget_range = lead_data.get("budget_range")
        if budget_range:
            budget_score = BUDGET_SCORES.get(budget_range, 0)
            score += budget_score
            if budget_score > 0:
                reasons.append(f"Budget range {budget_range} indicates potential for service match")

        # Timeline score
        timeline = lead_data.get("timeline")
        if timeline:
            timeline_score = TIMELINE_SCORES.get(timeline, 0)
            score += timeline_score
            if timeline_score > 0:
                reasons.append(f"Timeline {timeline} shows clear project planning")

        # Company information
        company = lead_data.get("company")
        if company and len(company.strip()) > 0:
            score += SCORE_WEIGHTS["company"]
            reasons.append("Has company information")

        # Message content
        message = lead_data.get("notes", "")
        if message:
            words = len(message.split())
            message_score = min(words / 20, 1.0) * SCORE_WEIGHTS["message"]
            score += message_score
            if message_score > SCORE_WEIGHTS["message"] / 2:
                reasons.append("Provided detailed inquiry")

        # Services interested
        services = lead_data.get("services_interested", [])
        if services:
            service_score = min(len(services), 3) * (SCORE_WEIGHTS["services"] / 3)
            score += service_score
            if service_score > 0:
                reasons.append(f"Interested in {len(services)} specific services")

        return {
            "score": min(score, 100),  # Cap at 100
            "reasons": reasons
        }

    async def _get_ai_analysis(self, lead_data: Dict[str, Any], conversation_history: Optional[List[Dict]] = None, shared_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get AI analysis of the lead using ModelManager with automatic fallback and performance tracking."""
        try:
            # Prepare input for AI analysis, incorporating shared context
            recommendations = shared_context.get("recommendations", {}) if shared_context else {}
            user_needs = shared_context.get("user_needs", []) if shared_context else []
            user_intent = shared_context.get("user_intent", "") if shared_context else ""
            analysis_prompt = {
                "lead": lead_data,
                "conversation_history": conversation_history or [],
                "service_recommendations": recommendations,
                "user_needs": user_needs,
                "user_intent": user_intent
            }

            # Use ModelManager for generation with lead_qualification task type, passing system prompt separately
            content = await self.model_manager.generate(
                prompt=f"Analyze this lead with shared context: {json.dumps(analysis_prompt)}",
                task_type="lead_qualification",
                system_prompt=self.config.system_prompt,
                temperature=self.config.temperature
            )

            # Extract JSON from response (handle potential markdown code blocks)
            json_match = re.search(r'```json\n(.*)\n```', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                # Try to find any JSON-like structure
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    analysis = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found in response")

            # Validate required fields
            required_fields = ["score", "confidence", "reasoning", "recommended_services",
                             "key_insights", "suggested_actions", "priority", "estimated_value"]
            if not all(field in analysis for field in required_fields):
                raise ValueError("Missing required fields in AI analysis")

            logger.info(f"AI analysis completed successfully for lead {lead_data.get('id', 'unknown')}")
            return analysis

        except Exception as e:
            logger.error(f"AI analysis failed with ModelManager: {e}")
            # Return conservative fallback analysis (ModelManager handles model fallback internally)
            return {
                "score": 50,  # Neutral score
                "confidence": 30,  # Low confidence due to error
                "reasoning": "Fallback analysis due to AI processing error",
                "recommended_services": lead_data.get("services_interested", []),
                "key_insights": ["Automated analysis unavailable"],
                "suggested_actions": ["Manual review required"],
                "priority": "medium",
                "estimated_value": 5000  # Conservative estimate
            }

    async def process_message(self, conversation_id: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process a message in the context of lead qualification."""
        try:
            # Get lead data from metadata
            lead_data = metadata.get("lead_data", {}) if metadata else {}
            if not lead_data:
                raise ValueError("No lead data provided in metadata")

            # Retrieve shared context from workflow
            recommendations = await self.get_shared_memory(conversation_id, "recommendations", scope="workflow")
            user_needs = await self.get_shared_memory(conversation_id, "user_needs", scope="workflow")
            user_intent = await self.get_shared_memory(conversation_id, "user_intent", scope="workflow")
            shared_context = {
                "recommendations": recommendations,
                "user_needs": user_needs,
                "user_intent": user_intent
            }

            # Calculate heuristic score
            heuristic_analysis = self._calculate_heuristic_score(lead_data)

            # Get AI analysis with shared context
            ai_analysis = await self._get_ai_analysis(lead_data, shared_context=shared_context)

            # Combine scores: 40% heuristic + 60% AI
            final_score = (heuristic_analysis["score"] * 0.4) + (ai_analysis["score"] * 0.6)

            # Prepare final analysis
            final_analysis = {
                "score": round(final_score, 1),
                "heuristic_score": round(heuristic_analysis["score"], 1),
                "ai_score": round(ai_analysis["score"], 1),
                "confidence": ai_analysis["confidence"],
                "reasoning": ai_analysis["reasoning"],
                "heuristic_reasons": heuristic_analysis["reasons"],
                "recommended_services": ai_analysis["recommended_services"],
                "key_insights": ai_analysis["key_insights"],
                "suggested_actions": ai_analysis["suggested_actions"],
                "priority": ai_analysis["priority"],
                "estimated_value": ai_analysis["estimated_value"]
            }

            # Store qualification result in shared memory
            workflow_execution_id = metadata.get("workflow_execution_id") if metadata else None
            await self.set_shared_memory(conversation_id, "lead_qualification", final_analysis, scope="workflow", workflow_execution_id=workflow_execution_id)

            # If lead score is high, send message to appropriate agent for follow-up
            if final_score > 70:
                target_agent = "web_development" if "web" in str(recommendations).lower() else "digital_marketing"
                await orchestrator.send_agent_message(
                    workflow_execution_id or "",
                    self.config.agent_id,
                    target_agent,
                    "notification",
                    {"lead_score": final_score, "priority": "high", "recommended_services": ai_analysis["recommended_services"]}
                )

            # Store lead priority in shared memory
            await self.set_shared_memory(conversation_id, "lead_priority", ai_analysis["priority"], scope="workflow", workflow_execution_id=workflow_execution_id)

            # Update lead score in Supabase
            try:
                supabase = get_supabase_client()
                await supabase.table("leads").update({
                    "lead_score": final_score,
                    "metadata": {
                        "last_analysis": final_analysis,
                        "last_analyzed_at": datetime.utcnow().isoformat()
                    }
                }).eq("id", lead_data["id"]).execute()
            except Exception as e:
                logger.error(f"Failed to update lead score: {e}")

            # Log the interaction
            await self._log_interaction(
                conversation_id=conversation_id,
                action="qualify_lead",
                input_data={"lead_data": lead_data, "message": message},
                output_data=final_analysis
            )

            return AgentResponse(
                content=json.dumps(final_analysis, indent=2),
                agent_id=self.config.agent_id,
                conversation_id=conversation_id,
                metadata=final_analysis,
                tools_used=[],
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.exception(f"Lead qualification failed: {e}")
            await self._log_interaction(
                conversation_id=conversation_id,
                action="qualify_lead",
                input_data={"message": message, "metadata": metadata},
                output_data={},
                error_message=str(e)
            )
            raise

    async def handle_agent_messages(self, workflow_execution_id: str) -> List[Dict[str, Any]]:
        """Handle incoming agent messages for lead qualification requests."""
        messages = await orchestrator.get_agent_messages(self.config.agent_id, workflow_execution_id)
        processed_responses = []
        for msg in messages:
            if msg["message_type"] == "request" and "lead_data" in msg["content"]:
                # Process lead qualification request from another agent
                lead_data = msg["content"]["lead_data"]
                conversation_id = msg["content"].get("conversation_id", "")
                # Perform qualification (reuse process_message logic if needed, or simplified)
                heuristic_analysis = self._calculate_heuristic_score(lead_data)
                ai_analysis = await self._get_ai_analysis(lead_data)
                final_score = (heuristic_analysis["score"] * 0.4) + (ai_analysis["score"] * 0.6)
                response_content = {
                    "lead_score": round(final_score, 1),
                    "priority": ai_analysis["priority"],
                    "recommended_services": ai_analysis["recommended_services"]
                }
                # Send response back
                await orchestrator.send_agent_message(
                    workflow_execution_id,
                    self.config.agent_id,
                    msg["from_agent"],
                    "response",
                    response_content
                )
                processed_responses.append({"message_id": msg["id"], "response": response_content})
        return processed_responses
