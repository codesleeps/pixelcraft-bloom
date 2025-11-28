from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import time
from ..models.manager import ModelManager
from ..models.config import MODELS, MODEL_PRIORITIES
from ..utils.limiter import limiter

import logging

logger = logging.getLogger(__name__)

# TODO: Implement proper authentication dependency
# from ..dependencies import get_current_user

# Global ModelManager instance - to be set in main.py
model_manager_instance: Optional[ModelManager] = None

def set_model_manager(mm: ModelManager):
    global model_manager_instance
    model_manager_instance = mm

def get_model_manager() -> Optional[ModelManager]:
    if model_manager_instance is None:
        logger.warning("ModelManager not initialized")
        return None
    return model_manager_instance

# Pydantic models for API requests/responses
class ModelInfo(BaseModel):
    name: str
    provider: str
    health: bool
    metrics: Dict[str, Any]

class ModelListResponse(BaseModel):
    models: List[ModelInfo]

class ModelTestRequest(BaseModel):
    model_name: str
    prompt: str
    task_type: str = "chat"
    system_prompt: Optional[str] = None

class ModelTestResponse(BaseModel):
    response: str
    latency: float
    tokens: int

class ModelGenerateRequest(BaseModel):
    model_name: str
    prompt: str
    task_type: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ModelGenerateResponse(BaseModel):
    response: str
    model_used: str
    latency: float

class ModelChatRequest(BaseModel):
    model_name: str
    messages: List[Dict[str, str]]
    task_type: str = "chat"
    temperature: Optional[float] = None

class ModelChatResponse(BaseModel):
    response: str
    model_used: str
    latency: float

class ModelHealthResponse(BaseModel):
    overall_health: bool
    models_health: Dict[str, bool]

class ModelMetricsResponse(BaseModel):
    metrics: Dict[str, Dict[str, Any]]

class ModelWarmupRequest(BaseModel):
    model_names: Optional[List[str]] = None

class ModelWarmupResponse(BaseModel):
    warmed_up: List[str]

class TaskModelsResponse(BaseModel):
    task_type: str
    recommended_models: List[str]

class BenchmarkResult(BaseModel):
    model_name: str
    responses: List[str]
    avg_latency: float
    success_rate: float

class ModelBenchmarkRequest(BaseModel):
    model_names: List[str]
    prompts: List[str]
    task_type: str

class ModelBenchmarkResponse(BaseModel):
    results: List[BenchmarkResult]

router = APIRouter()

# TODO: Add rate limiting middleware or dependency
# For now, implement basic rate limiting per endpoint if needed

@router.get("/models", response_model=ModelListResponse)
async def list_models(mm: Optional[ModelManager] = Depends(get_model_manager)):
    """List all available models with health status"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    models = []
    for name, config in MODELS.items():
        health = mm._health_checks.get(name, False)
        metrics = mm.metrics.get(name, {})
        models.append(ModelInfo(
            name=name,
            provider=config.provider.value,
            health=health,
            metrics=metrics
        ))
    return ModelListResponse(models=models)

@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model(model_name: str, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Get specific model details and metrics"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    if model_name not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    config = MODELS[model_name]
    health = mm._health_checks.get(model_name, False)
    metrics = mm.metrics.get(model_name, {})
    
    return ModelInfo(
        name=model_name,
        provider=config.provider.value,
        health=health,
        metrics=metrics
    )

@router.post("/models/test", response_model=ModelTestResponse)
@limiter.limit("10/minute")
async def test_model(request: Request, request_body: ModelTestRequest, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Test a model with sample input"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    if request_body.model_name not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    start_time = time.time()
    try:
        # For testing, use the specified model directly
        # Note: This assumes ModelManager has a method to generate with specific model
        # For now, using task_type selection - TODO: enhance ModelManager to support specific model
        response = await mm.generate(
            request_body.prompt, 
            request_body.task_type, 
            request_body.system_prompt
        )
        latency = time.time() - start_time
        tokens = len(response.split())  # Rough token estimate
        
        return ModelTestResponse(
            response=response,
            latency=latency,
            tokens=tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model test failed: {str(e)}")

@router.post("/models/generate", response_model=ModelGenerateResponse)
@limiter.limit("10/minute")
async def generate_completion(request: Request, request_body: ModelGenerateRequest, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Generate completion using specified model"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    if request_body.model_name not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    start_time = time.time()
    try:
        # TODO: Modify ModelManager.generate to accept specific model_name
        # For now, using task_type selection
        response = await mm.generate(
            request_body.prompt,
            request_body.task_type,
            request_body.system_prompt,
            temperature=request_body.temperature,
            max_tokens=request_body.max_tokens
        )
        latency = time.time() - start_time
        
        # TODO: Get actual model used from ModelManager
        return ModelGenerateResponse(
            response=response,
            model_used="selected_by_manager",  # Placeholder
            latency=latency
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/models/chat", response_model=ModelChatResponse)
@limiter.limit("10/minute")
async def chat_completion(request: Request, request_body: ModelChatRequest, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Chat completion using specified model"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    if request_body.model_name not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    start_time = time.time()
    try:
        # Convert messages to prompt format
        # TODO: Enhance ModelManager to support chat format directly
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in request_body.messages])
        
        response = await mm.generate(
            prompt,
            request_body.task_type,
            temperature=request_body.temperature
        )
        latency = time.time() - start_time
        
        return ModelChatResponse(
            response=response,
            model_used="selected_by_manager",  # Placeholder
            latency=latency
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@router.get("/models/health", response_model=ModelHealthResponse)
async def get_model_health(mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Overall model system health check"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    overall_health = all(mm._health_checks.values())
    return ModelHealthResponse(
        overall_health=overall_health,
        models_health=mm._health_checks
    )

@router.get("/models/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Get aggregated model performance metrics"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    return ModelMetricsResponse(metrics=mm.metrics)

@router.post("/models/warmup", response_model=ModelWarmupResponse)
async def warmup_models(request: ModelWarmupRequest, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Warm up models on demand"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    models_to_warm = request.model_names or list(MODELS.keys())
    warmed_up = []
    
    for model_name in models_to_warm:
        if model_name in MODELS and mm._health_checks.get(model_name, False):
            try:
                await mm.generate("Warm up test message.", "chat", max_tokens=10)
                warmed_up.append(model_name)
            except Exception as e:
                # Log error but continue
                pass
    
    return ModelWarmupResponse(warmed_up=warmed_up)

@router.get("/models/tasks/{task_type}", response_model=TaskModelsResponse)
async def get_recommended_models(task_type: str, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Get recommended models for task type"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    if task_type not in MODEL_PRIORITIES:
        raise HTTPException(status_code=404, detail="Task type not found")
    
    priority = MODEL_PRIORITIES[task_type]
    recommended_models = [
        model for model in priority.models + [priority.fallback_model]
        if mm._health_checks.get(model, False)
    ]
    
    return TaskModelsResponse(
        task_type=task_type,
        recommended_models=recommended_models
    )

@router.post("/models/benchmark", response_model=ModelBenchmarkResponse)
async def benchmark_models(request: ModelBenchmarkRequest, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Run benchmark tests on models"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    results = []
    
    for model_name in request.model_names:
        if model_name not in MODELS:
            continue
        
        responses = []
        latencies = []
        successes = 0
        
        for prompt in request.prompts:
            try:
                start_time = time.time()
                response = await mm.generate(prompt, request.task_type)
                latency = time.time() - start_time
                responses.append(response)
                latencies.append(latency)
                successes += 1
            except Exception as e:
                responses.append("")
                latencies.append(0.0)
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        success_rate = successes / len(request.prompts) if request.prompts else 0.0
        
        results.append(BenchmarkResult(
            model_name=model_name,
            responses=responses,
            avg_latency=avg_latency,
            success_rate=success_rate
        ))
    
    return ModelBenchmarkResponse(results=results)
