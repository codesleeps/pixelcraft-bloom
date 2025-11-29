from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
import os

# Use OLLAMA_HOST environment variable when available so endpoints work inside
# Docker Compose networks (service hostname `ollama`). Fall back to localhost.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
  
class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    HUGGING_FACE = "huggingface"
  
class ModelConfig(BaseModel):
    name: str
    provider: ModelProvider
    endpoint: str
    api_key: Optional[str] = None
    parameters: Dict = Field(default_factory=dict)
    timeout: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7
    context_window: int = 4096
    capabilities: Dict[str, bool] = Field(default_factory=lambda: {
        "chat": False,
        "completion": False,
        "embedding": False,
        "code_completion": False,
        "vision": False  # Added for enhanced capability flags
    })
    health_check_interval: int = 300  # seconds
    retry_attempts: int = 3
    cost_per_token: Optional[float] = None  # For HuggingFace API usage
    supports_streaming: bool = False
    supports_functions: bool = False
  
class ModelPriority(BaseModel):
    task_type: str
    models: List[str]  # In order of preference
    fallback_model: str
  
# Model configurations
MODELS = {
    "mistral": ModelConfig(
        name="mistral:latest",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 4,
            "top_k": 50,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        },
        max_tokens=4096,
        context_window=8192,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": True,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True
    ),
    "llama2": ModelConfig(
        name="llama2:7b",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 4,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        },
        context_window=4096,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": True,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True
    ),
    "llama3": ModelConfig(
        name="llama3.1:8b",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 8192,
            "num_thread": 4,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        },
        context_window=8192,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": True,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True
    ),
    "codellama": ModelConfig(
        name="codellama:latest",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 4,
            "top_k": 40,
            "top_p": 0.95,
            "repeat_penalty": 1.1
        },
        temperature=0.5,
        context_window=4096,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": True,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True
    ),
    "mixtral": ModelConfig(
        name="mixtral:latest",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 32768,
            "num_thread": 8,
            "top_k": 50,
            "top_p": 0.95,
            "repeat_penalty": 1.1
        },
        max_tokens=8192,
        context_window=32768,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": False,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True
    )
}
  
# Task-specific model priorities
MODEL_PRIORITIES = {
    "chat": ModelPriority(
        task_type="chat",
        models=["mistral", "llama3", "llama2"],
        fallback_model="mixtral"
    ),
    "code": ModelPriority(
        task_type="code",
        models=["codellama", "mistral", "llama3"],
        fallback_model="mixtral"
    ),
    "lead_qualification": ModelPriority(
        task_type="lead_qualification",
        models=["mistral", "llama3", "llama2"],
        fallback_model="mixtral"
    ),
    "service_recommendation": ModelPriority(
        task_type="service_recommendation",
        models=["mistral", "llama3", "llama2"],
        fallback_model="mixtral"
    ),
    "web_development": ModelPriority(  # Added for web_development agent task type
        task_type="web_development",
        models=["codellama", "mistral", "llama3"],
        fallback_model="mixtral"
    ),
    "digital_marketing": ModelPriority(
        task_type="digital_marketing",
        models=["mistral", "llama3", "llama2"],
        fallback_model="mixtral"
    ),
    "brand_design": ModelPriority(
        task_type="brand_design",
        models=["mistral", "llama3", "llama2"],
        fallback_model="mixtral"
    ),
    "ecommerce_solutions": ModelPriority(
        task_type="ecommerce_solutions",
        models=["mistral", "llama3", "codellama"],
        fallback_model="mixtral"
    ),
    "content_creation": ModelPriority(
        task_type="content_creation",
        models=["mistral", "llama3", "llama2"],
        fallback_model="mixtral"
    ),
    "analytics_consulting": ModelPriority(
        task_type="analytics_consulting",
        models=["mistral", "llama3", "codellama"],
        fallback_model="mixtral"
    )
}
