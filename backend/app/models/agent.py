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


class WorkflowExecutionRequest(BaseModel):
    workflow_type: str = Field(..., description="Type of workflow: multi_agent, conditional, sequential")
    conversation_id: str
    participating_agents: List[str]
    workflow_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration including routing rules")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    workflow_id: str
    conversation_id: str
    workflow_type: str
    current_state: str
    current_step: Optional[str] = None
    participating_agents: List[str]
    results: Dict[str, Any] = Field(default_factory=dict)
    started_at: str
    completed_at: Optional[str] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None


class WorkflowStateUpdate(BaseModel):
    workflow_id: str
    current_state: str
    current_step: Optional[str] = None
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class AgentMessageRequest(BaseModel):
    workflow_execution_id: str
    from_agent: str
    to_agent: str
    message_type: str = Field(..., description="Type: request, response, notification, handoff")
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class AgentMessageResponse(BaseModel):
    message_id: str
    workflow_execution_id: str
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    status: str
    created_at: str
    processed_at: Optional[str] = None


class WorkflowVisualizationResponse(BaseModel):
    workflow_id: str
    conversation_id: str
    workflow_type: str
    current_state: str
    execution_timeline: List[Dict[str, Any]]
    agent_interactions: List[Dict[str, Any]]
    shared_memory_keys: List[str]
    execution_graph: Dict[str, Any]
