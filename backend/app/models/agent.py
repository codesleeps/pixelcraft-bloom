from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    type: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    status: str = Field("inactive")


class AgentRequest(BaseModel):
    agent_type: str
    input_data: Dict[str, Any]
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class AgentResponse(BaseModel):
    agent_id: str
    result: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    status: str = Field("success")
    error: Optional[str] = None


class AgentListResponse(BaseModel):
    agents: List[AgentInfo] = Field(default_factory=list)
    total: int = 0
