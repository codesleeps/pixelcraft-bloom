from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

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

class ModelPriority(BaseModel):
    task_type: str
    models: List[str]  # In order of preference
    fallback_model: str

# Model configurations
MODELS = {
    "mistral": ModelConfig(
        name="mistral",
        provider=ModelProvider.OLLAMA,
        endpoint="http://localhost:11434/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 4,
            "top_k": 50,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    ),
    "llama2": ModelConfig(
        name="llama2",
        provider=ModelProvider.OLLAMA,
        endpoint="http://localhost:11434/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 4,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    ),
    "codellama": ModelConfig(
        name="codellama",
        provider=ModelProvider.OLLAMA,
        endpoint="http://localhost:11434/api/generate",
        parameters={
            "num_ctx": 4096,
            "num_thread": 4,
            "top_k": 40,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
    ),
    "mixtral-8x7b": ModelConfig(
        name="mixtral-8x7b",
        provider=ModelProvider.HUGGING_FACE,
        endpoint="https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
        api_key="${HUGGING_FACE_API_KEY}",  # Will be replaced with actual key from env
        parameters={
            "max_new_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
    )
}

# Task-specific model priorities
MODEL_PRIORITIES = {
    "chat": ModelPriority(
        task_type="chat",
        models=["mistral", "llama2"],
        fallback_model="mixtral-8x7b"
    ),
    "code": ModelPriority(
        task_type="code",
        models=["codellama", "mistral"],
        fallback_model="mixtral-8x7b"
    ),
    "lead_qualification": ModelPriority(
        task_type="lead_qualification",
        models=["mistral", "llama2"],
        fallback_model="mixtral-8x7b"
    ),
    "service_recommendation": ModelPriority(
        task_type="service_recommendation",
        models=["mistral", "llama2"],
        fallback_model="mixtral-8x7b"
    )
}