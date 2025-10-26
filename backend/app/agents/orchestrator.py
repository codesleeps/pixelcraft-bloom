"""Agent orchestrator placeholder.

Provides AgentOrchestrator class with registry and routing logic placeholders.
Detailed multi-agent coordination will be implemented in the agents development phase.
"""
from typing import Dict, Any, Optional
from .base import BaseAgent, BaseAgentConfig


class AgentOrchestrator:
    def __init__(self):
        self.registry: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        self.registry[agent.cfg.agent_id] = agent

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self.registry.get(agent_id)

    async def invoke(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.get(agent_id)
        if not agent:
            raise RuntimeError("Agent not found")
        return await agent.run(input_data)


orchestrator = AgentOrchestrator()

# Attempt to auto-register built-in agents if available
try:
    from .chat_agent import ChatAgent
    from .lead_agent import LeadQualificationAgent
    # create default configs
    chat_cfg = BaseAgentConfig(agent_id="chat", name="Chat Agent", description="Conversational agent")
    lead_cfg = BaseAgentConfig(agent_id="lead_qualification", name="Lead Qualification Agent", description="Scores and qualifies leads")
    orchestrator.register(ChatAgent(chat_cfg))
    orchestrator.register(LeadQualificationAgent(lead_cfg))
except Exception:
    # Import failure means dependencies missing or module errors; keep registry empty
    pass
