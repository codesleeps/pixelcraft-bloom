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


class ModelInfo(BaseModel):
    """Detailed information about an AI model."""
    name: str = Field(..., description="Unique name of the model")
    provider: str = Field(..., description="Provider of the model (e.g., 'ollama', 'huggingface')")
    model_type: str = Field(..., description="Type of model (e.g., 'llm', 'embedding')")
    status: str = Field(..., description="Current status of the model ('available', 'unavailable', 'error')")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities (e.g., 'chat', 'generation')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model-specific parameters")
    last_health_check: Optional[str] = Field(None, description="Timestamp of last health check")
    health_score: Optional[float] = Field(None, description="Health score from 0.0 to 1.0")


class ModelListResponse(BaseModel):
    """Response for listing available models."""
    models: List[ModelInfo] = Field(default_factory=list, description="List of available models")
    total: int = Field(0, description="Total number of models")


class ModelTestRequest(BaseModel):
    """Request to test a specific model."""
    model_name: str = Field(..., description="Name of the model to test")
    input_text: str = Field(..., description="Input text for testing")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optional parameters for the test")


class ModelTestResponse(BaseModel):
    """Response from model testing."""
    success: bool = Field(..., description="Whether the test was successful")
    output: str = Field("", description="Generated output from the model")
    latency_ms: float = Field(0.0, description="Response latency in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    error: Optional[str] = Field(None, description="Error message if test failed")


class ModelGenerateRequest(BaseModel):
    """Request for text generation using a model."""
    model_name: str = Field(..., description="Name of the model to use")
    prompt: str = Field(..., description="Prompt for generation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Optional generation parameters")


class ModelGenerateResponse(BaseModel):
    """Response from text generation."""
    generated_text: str = Field("", description="Generated text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (latency, tokens, etc.)")


class ModelHealthResponse(BaseModel):
    """Overall model system health status."""
    overall_health: str = Field(..., description="Overall health status ('healthy', 'degraded', 'unhealthy')")
    models_health: List[Dict[str, Any]] = Field(default_factory=list, description="Health status of individual models")
    last_updated: str = Field(..., description="Timestamp of last health check")


class ModelMetricsResponse(BaseModel):
    """Aggregated model performance metrics."""
    total_requests: int = Field(0, description="Total number of requests")
    success_rate: float = Field(0.0, description="Success rate as a percentage")
    average_latency_ms: float = Field(0.0, description="Average response latency in milliseconds")
    total_tokens_used: int = Field(0, description="Total tokens used across all requests")
    model_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Metrics per model")


class ModelBenchmarkRequest(BaseModel):
    """Request to benchmark models."""
    models_to_test: List[str] = Field(..., description="List of model names to benchmark")
    test_prompts: List[str] = Field(..., description="List of test prompts")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Benchmark parameters")


class ModelBenchmarkResponse(BaseModel):
    """Response from model benchmarking."""
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Benchmark results per model")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Overall benchmark summary")
