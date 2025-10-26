"""Base agent utilities and classes for AgentScope integration.

This module establishes base classes and shared utilities for agents.
Detailed implementations will be added in the next phase.
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class BaseAgentConfig:
    agent_id: str
    name: str
    description: Optional[str] = None
    default_model: str = "llama3"
    temperature: float = 0.7


class BaseAgent:
    def __init__(self, cfg: BaseAgentConfig):
        self.cfg = cfg

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent. Concrete agents should override this method."""
        raise NotImplementedError()
