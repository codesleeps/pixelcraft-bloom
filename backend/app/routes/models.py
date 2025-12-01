from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
from datetime import datetime
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

class ModelMetrics(BaseModel):
    model_name: str
    task_type: str = "chat"
    success_rate: float
    avg_response_time: float
    cache_hit_rate: float
    total_requests: int
    total_tokens: int

class ModelMetricsResponse(BaseModel):
    metrics: List[ModelMetrics]

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

@router.get("/models/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mm: Optional[ModelManager] = Depends(get_model_manager)
):
    """Get aggregated model performance metrics"""
    if mm is None:
        raise HTTPException(status_code=503, detail="ModelManager not available")
    
    metrics_list = []
    
    # Try to fetch from Supabase if dates are provided
    if start_date:
        try:
            from ..utils.supabase_client import get_supabase_client
            sb = get_supabase_client()
            
            query = sb.table("model_metrics").select("*")
            # Simple timestamp filtering (assuming timestamp is stored as float/int in DB)
            # If stored as ISO string, we'd use string comparison. 
            # manager.py stores it as time.time() (float).
            if start_date:
                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.gte("timestamp", dt.timestamp())
            if end_date:
                dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.lte("timestamp", dt.timestamp())
                
            result = query.execute()
            data = result.data or []
            
            # Aggregate
            agg = {}
            for row in data:
                name = row['model_name']
                if name not in agg:
                    agg[name] = {'requests': 0, 'successes': 0, 'total_latency': 0.0, 'total_tokens': 0}
                
                m = agg[name]
                m['requests'] += 1
                if row['success']:
                    m['successes'] += 1
                m['total_latency'] += row['latency']
                m['total_tokens'] += row.get('token_usage', 0)
            
            for name, m in agg.items():
                reqs = m['requests']
                metrics_list.append(ModelMetrics(
                    model_name=name,
                    task_type="chat",
                    success_rate=(m['successes'] / reqs * 100) if reqs > 0 else 0,
                    avg_response_time=(m['total_latency'] / reqs * 1000) if reqs > 0 else 0,
                    cache_hit_rate=0.0, # Not tracked yet
                    total_requests=reqs,
                    total_tokens=m['total_tokens']
                ))
                
            return ModelMetricsResponse(metrics=metrics_list)
            
        except Exception as e:
            logger.error(f"Failed to fetch metrics from Supabase: {e}")
            # Fallback to in-memory
            pass

    # Fallback to in-memory aggregation
    for name, m in mm.metrics.items():
        reqs = m['requests']
        metrics_list.append(ModelMetrics(
            model_name=name,
            task_type="chat",
            success_rate=(m['successes'] / reqs * 100) if reqs > 0 else 0,
            avg_response_time=(m['total_latency'] / reqs * 1000) if reqs > 0 else 0,
            cache_hit_rate=0.0,
            total_requests=reqs,
            total_tokens=m['total_tokens']
        ))

    return ModelMetricsResponse(metrics=metrics_list)

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
