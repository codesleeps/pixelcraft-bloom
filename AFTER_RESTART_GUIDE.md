# After Restart - Quick Start Guide

**Status**: All code changes complete, ready to update Docker images  
**Date**: December 8, 2024

---

## 🎯 What You Need to Do After Restart

### Step 1: Start Docker Desktop

```bash
# Docker should start automatically after restart
# Or manually start it:
open -a Docker

# Wait for Docker to fully start (check menu bar icon)
```

### Step 2: Update Docker Images (Automated)

```bash
# Run the automated update script
./scripts/update-docker.sh
```

**This script will:**
- ✅ Check if Docker is running
- ✅ Verify .env configuration
- ✅ Stop running containers
- ✅ Rebuild backend image with latest code
- ✅ Start all services
- ✅ Test the endpoints
- ✅ Show you the results

**Expected output:**
```
==========================================
AgentsFlowAI - Docker Update Script
==========================================

✓ Docker is running
✓ .env file exists
✓ .env has correct nested configuration format

Stopping running containers...
✓ Containers stopped

Rebuilding backend image...
✓ Backend image rebuilt successfully

Starting services with updated images...
✓ Backend container is running
✓ Health endpoint responding
✓ Model endpoints responding
✓ Models showing health: true

✓ Docker images updated successfully!
```

---

## 🔧 Manual Update (If Script Fails)

If the automated script doesn't work, follow these manual steps:

### 1. Check Docker Status
```bash
docker info
# Should show Docker info without errors
```

### 2. Rebuild Backend Image
```bash
docker compose build backend
```

### 3. Restart Services
```bash
docker compose down
docker compose up -d
```

### 4. Verify Updates
```bash
# Wait for services to start
sleep 15

# Test health endpoint
curl http://localhost:8000/health | jq .

# Test model endpoints (THE NEW ENDPOINTS!)
curl http://localhost:8000/api/models | jq .

# Test specific model
curl http://localhost:8000/api/models/mistral | jq .
```

---

## ✅ What Was Changed

All these changes are now in your local files and ready to be built into Docker:

### 1. **backend/app/config.py**
- Added `model_config = {"env_nested_delimiter": "__"}`
- Enables proper nested configuration parsing

### 2. **backend/app/routes/models.py**
- ✅ Added `GET /api/models` endpoint
- ✅ Added `GET /api/models/{model_name}` endpoint
- ✅ Enhanced documentation

### 3. **backend/app/routes/websocket.py**
- Fixed websocket decorator
- Added proper docstring

### 4. **.env files**
- Updated to use `SUPABASE__URL`, `SUPABASE__KEY`, `SUPABASE__JWT_SECRET`
- Both `backend/.env` and root `.env` updated

---

## 📊 Expected Results

After updating Docker images, you should see:

### Health Endpoint
```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "services": {
    "supabase": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "ollama": {"status": "healthy"},
    "models": {"status": "healthy"}
  }
}
```

### Model List Endpoint (NEW!)
```bash
curl http://localhost:8000/api/models
```

```json
{
  "models": [
    {
      "name": "mistral",
      "provider": "ollama",
      "health": true,
      "metrics": {
        "success_rate": 0,
        "avg_latency_ms": 0,
        "capabilities": {
          "chat": true,
          "completion": true,
          "code_completion": true
        }
      }
    },
    {
      "name": "mixtral",
      "provider": "ollama",
      "health": true,
      "metrics": {...}
    }
  ]
}
```

### Model Details Endpoint (NEW!)
```bash
curl http://localhost:8000/api/models/mistral
```

```json
{
  "name": "mistral",
  "provider": "ollama",
  "health": true,
  "metrics": {
    "model_full_name": "mistral:7b",
    "endpoint": "http://ollama:11434/api/generate",
    "temperature": 0.7,
    "context_window": 8192,
    "max_tokens": 4096
  }
}
```

---

## 🚀 Quick Commands Reference

```bash
# Update Docker images (automated)
./scripts/update-docker.sh

# Or manual steps:
docker compose build backend
docker compose down
docker compose up -d

# View logs
docker compose logs -f backend

# Check running containers
docker compose ps

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/models
curl http://localhost:8000/api/models/mistral

# Pull Ollama models (if needed)
docker compose exec ollama ollama pull mistral:7b
docker compose exec ollama ollama pull mixtral:8x7b

# Restart specific service
docker compose restart backend

# Fresh start (removes volumes)
docker compose down -v
docker compose up -d
```

---

## 📚 Documentation Available

All documentation is ready for you:

1. **AFTER_RESTART_GUIDE.md** ← You are here
2. **DOCKER_UPDATE_GUIDE.md** - Detailed Docker update instructions
3. **SUCCESS_REPORT.md** - Test results from local testing
4. **ALL_TASKS_COMPLETE.md** - Complete task summary
5. **ops/PRODUCTION_READINESS_COMPLETE.md** - Production deployment guide
6. **DEPLOYMENT_QUICK_REFERENCE.md** - Quick reference card

---

## 🎯 Summary

**After restart, just run:**
```bash
./scripts/update-docker.sh
```

**This will:**
1. ✅ Rebuild Docker images with latest code
2. ✅ Update all services
3. ✅ Test the new endpoints
4. ✅ Confirm everything is working

**Expected result**: Model health endpoints working in Docker with `"health": true`

---

## 🆘 Troubleshooting

### Docker won't start after restart

```bash
# Check Docker Desktop status
ps aux | grep -i docker

# Try starting manually
open -a Docker

# Wait 30 seconds for full startup
sleep 30

# Verify
docker info
```

### Build fails

```bash
# Clear build cache
docker builder prune -a

# Rebuild without cache
docker compose build --no-cache backend
```

### Containers won't start

```bash
# Check logs
docker compose logs backend

# Check for port conflicts
lsof -ti:8000

# Kill conflicting processes
kill -9 $(lsof -ti:8000)

# Restart
docker compose up -d
```

### Endpoints return 404

```bash
# Verify image was rebuilt
docker images | grep agentsflowai-backend

# Check build date (should be today)
docker inspect agentsflowai-backend:dev | jq '.[0].Created'

# Force rebuild if needed
docker compose build --no-cache backend
docker compose up -d --force-recreate backend
```

---

## ✨ What's Complete

✅ **All production readiness tasks complete**  
✅ **Model health check endpoints added**  
✅ **Configuration fixed for Docker**  
✅ **All code tested locally**  
✅ **Documentation created**  
✅ **Update scripts ready**  

**Next**: Update Docker images and verify everything works!

---

**Last Updated**: December 8, 2024  
**Status**: Ready for Docker update after restart

🎉 **Everything is ready - just restart and run the update script!**
