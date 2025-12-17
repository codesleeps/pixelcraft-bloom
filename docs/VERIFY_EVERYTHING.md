# Verify Everything - Quick Guide

**Time**: 5-10 minutes  
**Goal**: Confirm all changes work locally and in Docker

---

## 🎯 Quick Start

### Option 1: Test Local Backend (if running)

```bash
./verify-local.sh
```

### Option 2: Test Docker

```bash
./verify-docker.sh
```

### Option 3: Update Docker & Test

```bash
./scripts/update-docker.sh
```

---

## 📋 What Gets Verified

### ✅ Health Endpoint
- Backend is responding
- All services are healthy
- Database connection works

### ✅ Model List Endpoint (NEW!)
- `/api/models` returns all models
- Models show `"health": true`
- Metrics are populated

### ✅ Model Details Endpoint (NEW!)
- `/api/models/{model_name}` works
- Returns detailed model info
- Shows configuration and metrics

---

## 🚀 Step-by-Step Verification

### Step 1: Check What's Running

```bash
# Check if local backend is running
curl http://localhost:8000/health

# Check Docker status
docker info

# Check Docker containers
docker compose ps
```

### Step 2: Choose Your Path

**If local backend is running:**
```bash
./verify-local.sh
```

**If you want to test Docker:**
```bash
# Stop local backend first (if running)
# Then update Docker
./scripts/update-docker.sh

# Or just verify existing Docker
./verify-docker.sh
```

### Step 3: Verify Results

All three endpoints should work:

1. **Health**: `http://localhost:8000/health`
2. **Models List**: `http://localhost:8000/api/models`
3. **Model Details**: `http://localhost:8000/api/models/mistral`

---

## ✅ Expected Results

### Health Endpoint
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

### Models List
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
        "total_requests": 0,
        "capabilities": {...}
      }
    }
  ]
}
```

### Model Details
```json
{
  "name": "mistral",
  "provider": "ollama",
  "health": true,
  "metrics": {
    "model_full_name": "mistral:7b",
    "endpoint": "http://ollama:11434/api/generate",
    "temperature": 0.7,
    "context_window": 8192
  }
}
```

---

## 🔧 Manual Testing

If scripts don't work, test manually:

```bash
# Test health
curl http://localhost:8000/health | python3 -m json.tool

# Test models list
curl http://localhost:8000/api/models | python3 -m json.tool

# Test specific model
curl http://localhost:8000/api/models/mistral | python3 -m json.tool

# Test another model
curl http://localhost:8000/api/models/mixtral | python3 -m json.tool
```

---

## 🐳 Docker-Specific Checks

```bash
# Check containers are running
docker compose ps

# View backend logs
docker compose logs backend --tail=50

# View all logs
docker compose logs --tail=100

# Restart backend
docker compose restart backend

# Rebuild and restart
docker compose build backend
docker compose up -d --force-recreate backend
```

---

## 📊 Success Checklist

- [ ] Backend responds on port 8000
- [ ] `/health` returns healthy status
- [ ] `/api/models` returns list of models
- [ ] Models show `"health": true`
- [ ] `/api/models/mistral` returns details
- [ ] No errors in logs
- [ ] Docker containers running (if using Docker)

---

## 🆘 Troubleshooting

### Port 8000 in use
```bash
# Find process
lsof -ti:8000

# Kill it
kill -9 $(lsof -ti:8000)
```

### Docker not running
```bash
# Start Docker Desktop
open -a Docker

# Wait 30 seconds
sleep 30

# Verify
docker info
```

### Backend won't start
```bash
# Check logs
docker compose logs backend

# Or for local:
cd backend
python -m uvicorn app.main:app --reload
```

### Models show health: false
This is expected if Ollama isn't running. The endpoints still work!

---

## 🎯 Quick Commands

```bash
# Local backend
cd backend && python -m uvicorn app.main:app --reload

# Docker update
./scripts/update-docker.sh

# Docker logs
docker compose logs -f backend

# Stop everything
docker compose down

# Fresh start
docker compose down -v
docker compose up -d
```

---

## ✨ What's New

These endpoints were just added:

1. **GET /api/models** - List all models with health
2. **GET /api/models/{model_name}** - Get model details

Both are fully documented and production-ready!

---

## 📚 Related Docs

- `AFTER_RESTART_GUIDE.md` - Post-restart instructions
- `DOCKER_UPDATE_GUIDE.md` - Detailed Docker guide
- `QUICK_VERIFICATION_GUIDE.md` - Original verification steps
- `APPLICATION_OVERVIEW.md` - What this app does

---

## 🚀 Next Steps

Once verification passes:

1. ✅ Everything works locally/Docker
2. 🚀 Deploy to Hostinger VPS
3. 🌐 Configure domain and SSL
4. 🎉 Go live!

See `HOSTINGER_DEPLOYMENT_GUIDE.md` for deployment steps.

---

**Ready to verify? Run:**

```bash
# For local testing
./verify-local.sh

# For Docker testing
./verify-docker.sh

# To update Docker and test
./scripts/update-docker.sh
```

🎉 **Let's make sure everything works!**
