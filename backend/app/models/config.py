from enum import Enum
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
# DEVELOPMENT NOTE: Using only mistral:latest for development on macOS Docker.
# To use additional models (llama2, llama3, codellama), ensure your system has
# at least 16GB available Docker memory. See README.md for configuration.
MODELS = {
    "tinyllama": ModelConfig(
        name="tinyllama:1.1b",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 2048,
            "num_thread": 2,
            "top_k": 50,
            "top_p": 0.95,
            "repeat_penalty": 1.0,
            "temperature": 0.9,  # Higher for more creative responses
            "num_predict": 2048   # Max tokens to generate
        },
        max_tokens=2048,
        context_window=2048,
        temperature=0.9,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": False,
            "code_completion": False,
            "vision": False
        },
        supports_streaming=False,
        timeout=60
    ),
    "mistral": ModelConfig(
        name="mistral:7b",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 6,  # Increased for better CPU utilization
            "top_k": 50,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "temperature": 0.7,  # Balanced for quality/speed
            "num_predict": 4096
        },
        max_tokens=4096,
        context_window=8192,
        temperature=0.7,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": True,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True,  # Enable streaming support
        timeout=120
    ),
    "glm4": ModelConfig(
        name="glm-4.6:cloud",
        provider=ModelProvider.OLLAMA,
        endpoint=f"{OLLAMA_HOST}/api/generate",
        parameters={
            "num_ctx": 8192,
            "num_thread": 4,
            "top_k": 50,
            "top_p": 0.8,  # Optimized for quality
            "repeat_penalty": 1.2,
            "temperature": 0.3,  # Lower for more deterministic responses
            "num_predict": 8192
        },
        max_tokens=8192,
        context_window=8192,
        temperature=0.3,
        capabilities={
            "chat": True,
            "completion": True,
            "embedding": True,
            "code_completion": True,
            "vision": False
        },
        supports_streaming=True,  # Enable streaming support
        timeout=180
    )
}

# Task-specific model priorities
# Using glm4 as primary model for cloud-based performance
# mistral:7b as secondary option when cloud is unavailable
# tinyllama as fallback for resource-constrained environments
MODEL_PRIORITIES = {
    "chat": ModelPriority(
        task_type="chat",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "code": ModelPriority(
        task_type="code",
        models=["mistral", "glm4", "tinyllama"],  # Mistral often better for code
        fallback_model="tinyllama"
    ),
    "lead_qualification": ModelPriority(
        task_type="lead_qualification",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "service_recommendation": ModelPriority(
        task_type="service_recommendation",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "web_development": ModelPriority(
        task_type="web_development",
        models=["mistral", "glm4", "tinyllama"],  # Mistral better for technical tasks
        fallback_model="tinyllama"
    ),
    "digital_marketing": ModelPriority(
        task_type="digital_marketing",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "brand_design": ModelPriority(
        task_type="brand_design",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "ecommerce_solutions": ModelPriority(
        task_type="ecommerce_solutions",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "content_creation": ModelPriority(
        task_type="content_creation",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    ),
    "analytics_consulting": ModelPriority(
        task_type="analytics_consulting",
        models=["glm4", "mistral", "tinyllama"],
        fallback_model="tinyllama"
    )
}
