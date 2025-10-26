from typing import Any, Dict
from .base import BaseAgent, BaseAgentConfig
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client
import logging

logger = logging.getLogger("pixelcraft.agents.lead")


class LeadQualificationAgent(BaseAgent):
    def __init__(self, cfg: BaseAgentConfig):
        super().__init__(cfg)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead data and return a structured analysis.

        input_data expected to contain the lead fields (name, email, message, services_interested, budget_range, timeline, source)
        """
        lead = input_data.get("lead") or input_data.get("lead_data") or input_data

        # Basic heuristic scoring
        score = 50
        reasons = []
        if lead.get("budget_range"):
            score += 20
            reasons.append("budget provided")
        if lead.get("company"):
            score += 10
            reasons.append("company provided")
        if len(lead.get("message", "")) > 100:
            score += 10
            reasons.append("detailed message")

        # Clamp
        score = max(0, min(100, score))

        # If Ollama available, ask model for a short analysis to enrich insights
        insights = []
        recommended = []
        try:
            model = get_ollama_client()
            prompt = f"Analyze this lead and return a short summary, recommended services and a score between 0 and 100. Lead data:\n{lead}"
            if hasattr(model, "chat"):
                resp = model.chat([{"role": "system", "content": "You are an expert lead qualifier."}, {"role": "user", "content": prompt}])
                text = resp.get("response") if isinstance(resp, dict) else str(resp)
            elif hasattr(model, "generate"):
                gen = model.generate(prompt)
                text = getattr(gen, "text", str(gen))
            else:
                text = ""

            if text:
                insights.append(text)
                recommended = [s.strip() for s in (lead.get("services_interested") or [])]
        except Exception as exc:
            logger.debug("Ollama not available for lead analysis: %s", exc)

        analysis = {
            "score": score,
            "confidence": 0.7,
            "factors": {"heuristics": len(reasons)},
            "priority": "high" if score > 70 else "medium" if score > 40 else "low",
            "insights": insights,
            "recommended_services": recommended,
        }

        # Persist analysis to agent_logs table if present
        try:
            sb = get_supabase_client()
            sb.table("agent_logs").insert({"type": "lead_analysis", "lead": lead, "analysis": analysis}).execute()
        except Exception:
            pass

        return analysis
