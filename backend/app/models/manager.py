import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import logging
import os
import time
import hashlib
from dotenv import load_dotenv
from cachetools import TTLCache
from .config import MODELS, MODEL_PRIORITIES, ModelProvider, ModelConfig, ModelPriority
from ..utils.ollama_client import get_ollama_client
from ..utils.supabase_client import get_supabase_client
from ..utils.redis_client import get_redis_client

load_dotenv()

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_checks: Dict[str, bool] = {}
        self._hf_api_key = os.getenv("HUGGING_FACE_API_KEY")
        self.ollama_client = get_ollama_client()
        self.supabase = get_supabase_client()
        # self.cache = TTLCache(maxsize=1000, ttl=3600) # Replaced by Redis
        self.metrics: Dict[str, Dict[str, Any]] = {}  # model -> {'requests': 0, 'successes': 0, 'total_latency': 0, 'total_tokens': 0}
        self.circuit_breaker: Dict[str, Dict[str, Any]] = {}  # model -> {'failures': 0, 'last_failure': 0, 'state': 'closed'}
        self.rate_limiter = asyncio.Semaphore(10)  # allow 10 concurrent requests
    
    async def initialize(self):
        """Initialize aiohttp session and run health checks"""
        self._session = aiohttp.ClientSession()
        await self._check_model_availability()
        await self.warm_up_models()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._session:
            await self._session.close()
    
    async def _check_model_availability(self):
        """Check which models are available"""
        logger.info("Starting model availability check...")
        for model_name, config in MODELS.items():
            try:
                if config.provider == ModelProvider.OLLAMA:
                    logger.info(f"Checking Ollama model: {model_name} (actual name: {config.name})")
                    is_available = await self.ollama_client.is_ready(config.name)
                    self._health_checks[model_name] = is_available
                    logger.info(f"Model {model_name} ({config.name}): {'✓ AVAILABLE' if is_available else '✗ UNAVAILABLE'}")
                else:  # HuggingFace
                    if not self._hf_api_key:
                        self._health_checks[model_name] = False
                        logger.info(f"Model {model_name}: ✗ UNAVAILABLE (no HF API key)")
                        continue
                    # Ping HuggingFace API with a lightweight request
                    headers = {"Authorization": f"Bearer {self._hf_api_key}"}
                    async with self._session.post(
                        config.endpoint,
                        headers=headers,
                        json={"inputs": "test", "parameters": {"max_new_tokens": 1}}
                    ) as response:
                        self._health_checks[model_name] = response.status == 200
                        logger.info(f"Model {model_name}: {'✓ AVAILABLE' if response.status == 200 else '✗ UNAVAILABLE'}")
            except Exception as e:
                logger.error(f"Error checking {model_name}: {str(e)}")
                self._health_checks[model_name] = False
        
        available_count = sum(1 for v in self._health_checks.values() if v)
        logger.info(f"Model availability check complete: {available_count}/{len(self._health_checks)} models available")
        logger.info(f"Health checks: {self._health_checks}")
    
    def get_available_models(self, task_type: str) -> List[ModelConfig]:
        """Get available models for a task in priority order, considering health and circuit breaker"""
        priority = MODEL_PRIORITIES.get(task_type)
        if not priority:
            raise ValueError(f"Unknown task type: {task_type}")

        models = []
        for model_name in priority.models + [priority.fallback_model]:
            if self._health_checks.get(model_name, False) and not self._is_circuit_open(model_name):
                models.append(MODELS[model_name])
        return models

    def _is_circuit_open(self, model_name: str) -> bool:
        cb = self.circuit_breaker.get(model_name, {'failures': 0, 'last_failure': 0, 'state': 'closed'})
        if cb['state'] == 'open':
            if time.time() - cb['last_failure'] > 60:  # reset after 60s
                cb['state'] = 'closed'
                cb['failures'] = 0
                self.circuit_breaker[model_name] = cb
                return False
            return True
        return False

    def _record_failure(self, model_name: str):
        cb = self.circuit_breaker.get(model_name, {'failures': 0, 'last_failure': 0, 'state': 'closed'})
        cb['failures'] += 1
        cb['last_failure'] = time.time()
        if cb['failures'] > 5:
            cb['state'] = 'open'
        self.circuit_breaker[model_name] = cb

    def _get_cache_key(self, model_name: str, prompt: str, system_prompt: str, kwargs: dict) -> str:
        key_data = f"{model_name}:{prompt}:{system_prompt}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_response(self, key: str) -> Optional[str]:
        redis = get_redis_client()
        if redis:
            val = redis.get(f"model_cache:{key}")
            return val.decode('utf-8') if val else None
        return None

    def _cache_response(self, key: str, response: str):
        redis = get_redis_client()
        if redis:
            redis.setex(f"model_cache:{key}", 3600, response)

    async def _update_metrics(self, model_name: str, latency: float, success: bool, token_usage: int = 0):
        if model_name not in self.metrics:
            self.metrics[model_name] = {'requests': 0, 'successes': 0, 'total_latency': 0, 'total_tokens': 0}
        m = self.metrics[model_name]
        m['requests'] += 1
        if success:
            m['successes'] += 1
        m['total_latency'] += latency
        m['total_tokens'] += token_usage
        # Persist to Supabase
        try:
            await self.supabase.table('model_metrics').insert({
                'model_name': model_name,
                'latency': latency,
                'success': success,
                'token_usage': token_usage,
                'timestamp': time.time()
            }).execute()
        except Exception as e:
            logger.error(f"Failed to persist metrics: {e}")
    
    async def generate(
        self,
        prompt: str,
        task_type: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using the appropriate model with caching, failover, and metrics"""
        async with self.rate_limiter:
            models = self.get_available_models(task_type)
            if not models:
                logger.warning("No available models, returning default response")
                return "I'm sorry, I'm currently unable to process your request due to all models being unavailable. Please try again later."

            logger.info(f"[ModelManager] Attempting generation for task_type={task_type}, available models: {[m.name for m in models]}")
            for model_config in models:
                cache_key = self._get_cache_key(model_config.name, prompt, system_prompt or '', kwargs)
                cached = self._get_cached_response(cache_key)
                if cached:
                    logger.debug(f"[ModelManager] Cache hit for {model_config.name}")
                    return cached
                start_time = time.time()
                try:
                    logger.info(f"[ModelManager] Trying model: {model_config.name} for task_type={task_type}")
                    response = await self._generate_with_config(
                        prompt,
                        model_config,
                        system_prompt,
                        **kwargs
                    )
                    latency = time.time() - start_time
                    logger.info(f"[ModelManager] ✓ Success with {model_config.name} (latency={latency:.2f}s)")
                    await self._update_metrics(model_config.name, latency, True, len(response.split()))  # rough token estimate
                    self._cache_response(cache_key, response)
                    return response
                except Exception as e:
                    latency = time.time() - start_time
                    logger.error(f"[ModelManager] ✗ Failed with {model_config.name}: {type(e).__name__} (latency={latency:.2f}s)")
                    logger.debug(f"[ModelManager] Error detail: {str(e)}")
                    await self._update_metrics(model_config.name, latency, False)
                    self._record_failure(model_config.name)
                    continue

            # If all failed
            logger.error(f"[ModelManager] All models exhausted for task_type={task_type}")
            return "I'm sorry, I'm currently unable to process your request due to model failures. Please try again later."
    
    async def _generate_with_config(
        self,
        prompt: str,
        model_config: ModelConfig,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        if model_config.provider == ModelProvider.OLLAMA:
            return await self._generate_ollama(prompt, model_config, system_prompt, **kwargs)
        else:
            return await self._generate_huggingface(prompt, model_config, system_prompt, **kwargs)

    async def _generate_ollama(
        self,
        prompt: str,
        model_config: ModelConfig,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate using Ollama via OllamaClient"""
        logger.info(f"[ModelManager] Attempting generation with model: {model_config.name}")
        if system_prompt:
            # Use chat API for system prompt support
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            logger.debug(f"[ModelManager] Using /api/chat for {model_config.name} with {len(messages)} messages")
            response = await self.ollama_client.chat(
                model=model_config.name,
                messages=messages,
                **model_config.parameters,
                **kwargs
            )
            logger.info(f"[ModelManager] ✓ Chat generation succeeded with {model_config.name}")
        else:
            # Use generate API for simple completion
            logger.debug(f"[ModelManager] Using /api/generate for {model_config.name}")
            response = await self.ollama_client.generate(
                model=model_config.name,
                prompt=prompt,
                **model_config.parameters,
                **kwargs
            )
            logger.info(f"[ModelManager] ✓ Generate succeeded with {model_config.name}")
        return response["message"]["content"]
    
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

    async def warm_up_models(self):
        """Warm up available models with a test prompt using long timeout and retries.
        
        This eagerly loads model runners at startup using the Ollama client's retry logic.
        Models are available for use even if warm-up fails (they'll load on first request).
        Warm-up just pre-loads them to avoid user-facing timeouts on the first request.
        """
        logger.info("Warming up models (this may take several minutes)...")
        for model_name, model_config in MODELS.items():
            if not self._health_checks.get(model_name, False):
                logger.debug(f"Skipping warm-up for {model_name}: marked unhealthy")
                continue
            
            if model_config.provider != "ollama":
                logger.debug(f"Skipping warm-up for non-Ollama model {model_name}")
                continue
            
            try:
                logger.info(f"[Warm-up] Loading {model_name}...")
                prompt = "Hello, this is a warm-up message."
                response = await self.ollama_client.generate(
                    model=model_config.name,
                    prompt=prompt,
                    max_tokens=10
                )
                logger.info(f"[Warm-up] ✓ Loaded {model_name}")
            except Exception as e:
                # Warm-up failures are non-critical: model will load on first user request
                logger.info(f"[Warm-up] ✗ Did not pre-load {model_name}: {type(e).__name__}. Will load on first use.")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        **kwargs
    ) -> str:
        """Perform a chat completion using the appropriate model with caching, failover, and metrics"""
        # Simple cache key based on messages
        cache_key = self._get_cache_key('', str(messages), '', kwargs)
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        async with self.rate_limiter:
            models = self.get_available_models(task_type)
            if not models:
                logger.warning("No available models, returning default response")
                return "I'm sorry, I'm currently unable to process your request due to all models being unavailable. Please try again later."

            for model_config in models:
                start_time = time.time()
                try:
                    response = await self._chat_with_config(messages, model_config, **kwargs)
                    latency = time.time() - start_time
                    await self._update_metrics(model_config.name, latency, True, len(response.split()))  # rough token estimate
                    self._cache_response(cache_key, response)
                    return response
                except Exception as e:
                    latency = time.time() - start_time
                    await self._update_metrics(model_config.name, latency, False)
                    self._record_failure(model_config.name)
                    logger.error(f"Failed with {model_config.name}: {e}")
                    continue

            # If all failed
            return "I'm sorry, I'm currently unable to process your request due to model failures. Please try again later."

    async def _chat_with_config(
        self,
        messages: List[Dict[str, str]],
        model_config: ModelConfig,
        **kwargs
    ) -> str:
        if model_config.provider == ModelProvider.OLLAMA:
            response = await self.ollama_client.chat(
                model=model_config.name,
                messages=messages,
                **model_config.parameters,
                **kwargs
            )
            return response["message"]["content"]
        else:
            # For HuggingFace, convert messages to prompt (simplified)
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            return await self._generate_huggingface(prompt, model_config, None, **kwargs)

    async def batch_generate(
        self,
        prompts: List[str],
        task_type: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """Generate responses for multiple prompts concurrently"""
        tasks = [self.generate(p, task_type, system_prompt, **kwargs) for p in prompts]
        return await asyncio.gather(*tasks)
