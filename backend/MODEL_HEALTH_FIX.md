# Model Health Check Fix

## Problem

All Ollama models were showing `"health": false` in the `/api/models` endpoint response:

```json
{
  "models": [
    {"name": "mistral", "provider": "ollama", "health": false},
    {"name": "llama3", "provider": "ollama", "health": false}
  ]
}
```

## Root Cause

The `/api/models` endpoint was **missing** from the backend API. The smoke test script (`scripts/smoke-test.sh`) was expecting these endpoints:

1. `GET /api/models` - List all models with health status
2. `GET /api/models/{model_name}` - Get specific model details

But only the following endpoints existed in `backend/app/routes/models.py`:
- `GET /api/models/metrics` - Performance metrics
- `GET /api/models/tasks/{task_type}` - Recommended models for task
- `POST /api/models/warmup` - Warm up models
- `POST /api/models/benchmark` - Benchmark models

## Solution

Added two new endpoints to `backend/app/routes/models.py`:

### 1. List All Models - `GET /api/models`

Returns a list of all configured models with their health status and metrics:

```python
@router.get("/models", response_model=ModelListResponse)
async def list_models(mm: Optional[ModelManager] = Depends(get_model_manager)):
    """List all available models with health status"""
    # Returns ModelListResponse with models array
```

**Response Example:**
```json
{
  "models": [
    {
      "name": "mistral",
      "provider": "ollama",
      "health": true,
      "metrics": {
        "success_rate": 95.5,
        "avg_latency_ms": 234.5,
        "total_requests": 150,
        "total_tokens": 45000,
        "capabilities": {
          "chat": true,
          "completion": true,
          "embedding": true,
          "code_completion": true,
          "vision": false
        },
        "context_window": 8192,
        "max_tokens": 4096
      }
    },
    {
      "name": "mixtral",
      "provider": "ollama",
      "health": true,
      "metrics": {
        "success_rate": 98.2,
        "avg_latency_ms": 456.7,
        "total_requests": 89,
        "total_tokens": 32000,
        "capabilities": {
          "chat": true,
          "completion": true,
          "embedding": true,
          "code_completion": true,
          "vision": false
        },
        "context_window": 32768,
        "max_tokens": 4096
      }
    }
  ]
}
```

### 2. Get Model Details - `GET /api/models/{model_name}`

Returns detailed information about a specific model:

```python
@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_details(model_name: str, mm: Optional[ModelManager] = Depends(get_model_manager)):
    """Get details for a specific model"""
    # Returns ModelInfo with detailed metrics
```

**Response Example:**
```json
{
  "name": "mistral",
  "provider": "ollama",
  "health": true,
  "metrics": {
    "success_rate": 95.5,
    "avg_latency_ms": 234.5,
    "total_requests": 150,
    "total_tokens": 45000,
    "capabilities": {
      "chat": true,
      "completion": true,
      "embedding": true,
      "code_completion": true,
      "vision": false
    },
    "context_window": 8192,
    "max_tokens": 4096,
    "model_full_name": "mistral:7b",
    "endpoint": "http://localhost:11434/api/generate",
    "temperature": 0.7,
    "supports_streaming": false,
    "supports_functions": false
  }
}
```

## Health Check Logic

The health status comes from `ModelManager._health_checks` dictionary, which is populated during initialization:

1. **Startup**: `ModelManager.initialize()` calls `_check_model_availability()`
2. **Ollama Models**: Uses `ollama_client.is_ready(model_name)` to check if model is available
3. **HuggingFace Models**: Pings the API endpoint with a test request
4. **Result**: Stored in `_health_checks` dict as `{model_name: bool}`

The health check runs:
- On backend startup
- After model warm-up
- Can be manually triggered via health check endpoint

## Testing

### 1. Start the Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. Run the Test Script

```bash
cd backend
python test_models_endpoint.py
```

Expected output:
```
============================================================
Testing Model Endpoints
============================================================
Testing /health endpoint...
✓ Health check: 200

Testing GET /api/models endpoint...
Status: 200
✓ Models endpoint working!
  Found 2 models:
  ✓ mistral (ollama)
    Health: True
    Success Rate: 0%
    Avg Latency: 0ms
    Total Requests: 0
  ✓ mixtral (ollama)
    Health: True
    Success Rate: 0%
    Avg Latency: 0ms
    Total Requests: 0

Testing GET /api/models/mistral endpoint...
Status: 200
✓ Model details endpoint working!
  Model: mistral
  Provider: ollama
  Health: True
  ...

============================================================
Test Summary
============================================================
✓ List Models
✓ Get Model Details

Passed: 2/2
✓ All tests passed!
```

### 3. Run Smoke Tests

```bash
./scripts/smoke-test.sh
```

Expected output:
```
--- Test 2: Models Endpoint ---
Testing Models List... ✓ PASS

--- Test 4: Model Details ---
Testing Model Details... ✓ PASS
```

## Manual Testing with curl

```bash
# List all models
curl http://localhost:8000/api/models | jq .

# Get specific model details
curl http://localhost:8000/api/models/mistral | jq .

# Check health
curl http://localhost:8000/health | jq .
```

## Files Modified

1. **backend/app/routes/models.py**
   - Added `list_models()` endpoint
   - Added `get_model_details()` endpoint

2. **backend/test_models_endpoint.py** (NEW)
   - Test script for verifying endpoints

3. **backend/MODEL_HEALTH_FIX.md** (NEW)
   - This documentation file

## Next Steps

After verifying the fix works:

1. ✅ Model health checks now return correct status
2. ⏭️ Continue with other production readiness tasks:
   - Environment variable validation
   - Database connection pooling
   - Redis retry logic
   - Per-user rate limiting

## Troubleshooting

### Models show health: false

**Possible causes:**
1. Ollama is not running
   - Start with: `ollama serve`
2. Models not pulled
   - Pull with: `ollama pull mistral:7b`
3. Wrong OLLAMA_HOST in .env
   - Check: `echo $OLLAMA_HOST`
   - Should be: `http://localhost:11434` (or `http://ollama:11434` in Docker)

### Endpoint returns 503

**Cause:** ModelManager not initialized

**Solution:** Check backend logs for initialization errors:
```bash
# Look for these log messages:
# "ModelManager initialized, available models: ..."
# "Ollama ready=True"
```

### Endpoint returns 404

**Cause:** Router not included in main app

**Solution:** Verify in `backend/app/main.py`:
```python
app.include_router(models_routes.router, prefix="/api")
```

## Related Documentation

- [Backend README](./README.md) - API documentation
- [Smoke Test Script](../scripts/smoke-test.sh) - Automated testing
- [Production Readiness](../ops/PRODUCTION_READINESS.md) - Deployment checklist
