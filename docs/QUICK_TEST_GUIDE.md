# Quick Test Guide - Model Health Check Fix

## Prerequisites

1. **Ollama Running**
   ```bash
   ollama serve
   ```

2. **Models Pulled**
   ```bash
   ollama pull mistral:7b
   ollama pull mixtral:8x7b
   ```

3. **Backend Dependencies Installed**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

## Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Wait for these log messages:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
[ModelManager] Model availability check complete: 2/2 models available
```

## Test Methods

### Method 1: Automated Test Script (Recommended)

```bash
# In a new terminal
cd backend
python test_models_endpoint.py
```

**Expected Output:**
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
  ✓ mixtral (ollama)
    Health: True

Testing GET /api/models/mistral endpoint...
Status: 200
✓ Model details endpoint working!

============================================================
Test Summary
============================================================
✓ List Models
✓ Get Model Details

Passed: 2/2
✓ All tests passed!
```

### Method 2: Smoke Test Suite

```bash
./scripts/smoke-test.sh
```

**Expected Output:**
```
--- Test 2: Models Endpoint ---
Testing Models List... ✓ PASS

--- Test 4: Model Details ---
Testing Model Details... ✓ PASS

========================================
Test Results:
Passed: 4
Failed: 0
========================================
✓ All smoke tests passed!
```

### Method 3: Manual curl Commands

```bash
# Test 1: List all models
curl http://localhost:8000/api/models | jq .

# Test 2: Get mistral details
curl http://localhost:8000/api/models/mistral | jq .

# Test 3: Get mixtral details
curl http://localhost:8000/api/models/mixtral | jq .

# Test 4: Check overall health
curl http://localhost:8000/health | jq .
```

### Method 4: Browser Testing

Open in browser:
- http://localhost:8000/docs (Swagger UI)
- Navigate to "GET /api/models"
- Click "Try it out" → "Execute"

## Troubleshooting

### Issue: "health": false for all models

**Check 1: Is Ollama running?**
```bash
curl http://localhost:11434/api/tags
```
Should return list of models. If not, start Ollama:
```bash
ollama serve
```

**Check 2: Are models pulled?**
```bash
ollama list
```
Should show mistral:7b and mixtral:8x7b. If not:
```bash
ollama pull mistral:7b
ollama pull mixtral:8x7b
```

**Check 3: Check backend logs**
```bash
# Look for these messages in backend terminal:
# "Checking Ollama model: mistral (actual name: mistral:7b)"
# "Model mistral (mistral:7b): ✓ AVAILABLE"
```

### Issue: 503 Service Unavailable

**Cause:** ModelManager not initialized

**Solution:** Check backend startup logs for errors:
```bash
# Look for:
# "ModelManager initialized, available models: ['mistral', 'mixtral']"
```

If you see errors, check:
1. Ollama connection: `curl http://localhost:11434/api/tags`
2. Environment variables: `cat backend/.env | grep OLLAMA`

### Issue: 404 Not Found

**Cause:** Endpoints not registered

**Solution:** Verify router is included in `backend/app/main.py`:
```python
app.include_router(models_routes.router, prefix="/api")
```

### Issue: Connection Refused

**Cause:** Backend not running

**Solution:** Start backend:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

## Success Criteria

✅ All tests pass  
✅ Models show `"health": true`  
✅ Metrics are populated after making requests  
✅ No errors in backend logs  

## Next Steps After Verification

1. Commit the changes:
   ```bash
   git add backend/app/routes/models.py
   git add backend/test_models_endpoint.py
   git add backend/MODEL_HEALTH_FIX.md
   git add ops/PRODUCTION_READINESS.md
   git commit -m "Fix: Add missing /api/models endpoints for health checks"
   ```

2. Move to next production readiness task:
   - Environment variable validation
   - Database connection pooling
   - Redis retry logic

## Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Overall system health |
| `/api/models` | GET | List all models with health |
| `/api/models/{name}` | GET | Get specific model details |
| `/api/models/metrics` | GET | Performance metrics |
| `/api/models/warmup` | POST | Warm up models |

## Documentation

- **Fix Details**: `backend/MODEL_HEALTH_FIX.md`
- **Task Summary**: `TASK_COMPLETION_SUMMARY.md`
- **Backend API**: `backend/README.md`
- **Production Checklist**: `ops/PRODUCTION_READINESS.md`
