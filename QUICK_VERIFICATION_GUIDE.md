# Quick Verification Guide

**Test locally first, then Docker**  
**Time**: 10-15 minutes

---

## ✅ Step 1: Test Locally (Current Setup)

Your local backend should still be running from earlier. Let's verify:

```bash
# Check if backend is running
curl http://localhost:8000/health

# Test model endpoints
curl http://localhost:8000/api/models | jq .

# Run automated tests
python backend/test_models_endpoint.py
```

**Expected**: All tests pass ✅

If backend isn't running:
```bash
cd backend
python -m uvicorn app.main:app --reload
```

---

## ✅ Step 2: Test with Docker

### 2.1 Stop Local Backend First

```bash
# Stop the local backend (Ctrl+C in the terminal where it's running)
# Or find and kill the process:
lsof -ti:8000 | xargs kill -9
```

### 2.2 Start Docker (if not already running)

```bash
# Check if Docker is running
docker info

# If not, start Docker Desktop
open -a Docker

# Wait for Docker to start (30 seconds)
```

### 2.3 Run the Update Script

```bash
# This rebuilds images and starts services
./scripts/update-docker.sh
```

**Expected output:**
```
✓ Docker is running
✓ .env file exists
✓ Backend image rebuilt successfully
✓ Backend container is running
✓ Health endpoint responding
✓ Model endpoints responding
✓ Models showing health: true
```

### 2.4 Manual Verification (if script fails)

```bash
# Rebuild and start
docker compose build backend
docker compose down
docker compose up -d

# Wait for startup
sleep 15

# Check containers
docker compose ps

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/models
```

---

## ✅ Step 3: Verify Everything Works

### Test Health Endpoint
```bash
curl http://localhost:8000/health | jq .
```

**Expected:**
```json
{
  "status": "healthy",
  "services": {
    "supabase": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "models": {"status": "healthy"}
  }
}
```

### Test Model Endpoints
```bash
curl http://localhost:8000/api/models | jq .
```

**Expected:**
```json
{
  "models": [
    {
      "name": "mistral",
      "provider": "ollama",
      "health": true,
      "metrics": {...}
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

### Test Specific Model
```bash
curl http://localhost:8000/api/models/mistral | jq .
```

**Expected:** Detailed model info with `"health": true`

### Check Docker Logs
```bash
docker compose logs backend --tail=50
```

**Expected:** No errors, should see:
```
INFO:     Application startup complete.
INFO:     ModelManager initialized, available models: ['mistral', 'mixtral']
```

---

## ✅ Step 4: Quick Checklist

- [ ] Local backend works (if testing locally)
- [ ] Docker is running
- [ ] Docker images rebuilt successfully
- [ ] All containers are up (`docker compose ps`)
- [ ] Health endpoint returns 200
- [ ] Models endpoint returns list
- [ ] Models show `"health": true`
- [ ] No errors in logs

---

## 🎯 Success Criteria

Everything is working when:

✅ **Local**: Backend responds on http://localhost:8000  
✅ **Docker**: All containers running  
✅ **Health**: `/health` returns healthy status  
✅ **Models**: `/api/models` shows health: true  
✅ **Logs**: No errors in `docker compose logs`  

---

## 🆘 Quick Troubleshooting

### Docker won't start
```bash
# Restart Docker Desktop
# macOS: Quit and reopen Docker Desktop app
```

### Port 8000 already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Then restart Docker
docker compose up -d
```

### Containers won't start
```bash
# Check logs
docker compose logs

# Rebuild without cache
docker compose build --no-cache backend
docker compose up -d
```

### Models show health: false
```bash
# This is expected if Ollama isn't running
# In Docker, Ollama should start automatically
# Check Ollama container:
docker compose ps ollama
docker compose logs ollama
```

---

## 🚀 You're Ready!

Once both local and Docker tests pass, you're ready to:

1. ✅ Deploy to Hostinger VPS
2. ✅ Configure domain and SSL
3. ✅ Go live!

---

**Quick Commands Reference:**

```bash
# Local
cd backend && python -m uvicorn app.main:app --reload

# Docker
./scripts/update-docker.sh

# Test
curl http://localhost:8000/api/models

# Logs
docker compose logs -f backend

# Stop
docker compose down
```

---

**Everything ready? Let's deploy! 🎉**
