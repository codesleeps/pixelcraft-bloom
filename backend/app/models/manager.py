import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import logging
import os
from dotenv import load_dotenv
from .config import MODELS, MODEL_PRIORITIES, ModelProvider, ModelConfig, ModelPriority

load_dotenv()

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_checks: Dict[str, bool] = {}
        self._hf_api_key = os.getenv("HUGGING_FACE_API_KEY")
    
    async def initialize(self):
        """Initialize aiohttp session and run health checks"""
        self._session = aiohttp.ClientSession()
        await self._check_model_availability()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._session:
            await self._session.close()
    
    async def _check_model_availability(self):
        """Check which models are available"""
        for model_name, config in MODELS.items():
            try:
                if config.provider == ModelProvider.OLLAMA:
                    # Ping Ollama API
                    async with self._session.get(
                        "http://localhost:11434/api/tags"
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            models = [model["name"] for model in data["models"]]
                            self._health_checks[model_name] = model_name in models
                        else:
                            self._health_checks[model_name] = False
                else:  # HuggingFace
                    if not self._hf_api_key:
                        self._health_checks[model_name] = False
                        continue
                    
                    # Ping HuggingFace API
                    headers = {"Authorization": f"Bearer {self._hf_api_key}"}
                    async with self._session.get(
                        config.endpoint,
                        headers=headers
                    ) as response:
                        self._health_checks[model_name] = response.status == 200
            
            except Exception as e:
                logger.error(f"Error checking {model_name}: {str(e)}")
                self._health_checks[model_name] = False
    
    def get_available_model(self, task_type: str) -> ModelConfig:
        """Get the first available model for a task"""
        priority = MODEL_PRIORITIES.get(task_type)
        if not priority:
            raise ValueError(f"Unknown task type: {task_type}")
        
        # Try primary models first
        for model_name in priority.models:
            if self._health_checks.get(model_name, False):
                return MODELS[model_name]
        
        # Try fallback model
        if self._health_checks.get(priority.fallback_model, False):
            return MODELS[priority.fallback_model]
        
        raise RuntimeError(f"No available models for task type: {task_type}")
    
    async def generate(
        self,
        prompt: str,
        task_type: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using the appropriate model"""
        model_config = self.get_available_model(task_type)
        
        try:
            if model_config.provider == ModelProvider.OLLAMA:
                return await self._generate_ollama(
                    prompt,
                    model_config,
                    system_prompt,
                    **kwargs
                )
            else:
                return await self._generate_huggingface(
                    prompt,
                    model_config,
                    system_prompt,
                    **kwargs
                )
        except Exception as e:
            logger.error(f"Error generating with {model_config.name}: {str(e)}")
            raise
    
    async def _generate_ollama(
        self,
        prompt: str,
        model_config: ModelConfig,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate using Ollama"""
        payload = {
            "model": model_config.name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            **model_config.parameters,
            **kwargs
        }
        
        async with self._session.post(model_config.endpoint, json=payload) as response:
            if response.status != 200:
                raise RuntimeError(f"Ollama API error: {response.status}")
            
            data = await response.json()
            return data["response"]
    
    async def _generate_huggingface(
        self,
        prompt: str,
        model_config: ModelConfig,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate using HuggingFace"""
        headers = {"Authorization": f"Bearer {self._hf_api_key}"}
        
        # Format prompt for instruction models
        if system_prompt:
            formatted_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
        else:
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        
        payload = {
            "inputs": formatted_prompt,
            "parameters": {
                **model_config.parameters,
                **kwargs
            }
        }
        
        async with self._session.post(
            model_config.endpoint,
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"HuggingFace API error: {response.status}")
            
            data = await response.json()
            return data[0]["generated_text"]