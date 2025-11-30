# PixelCraft Bloom - Operations Runbook

This runbook provides step-by-step instructions for operating, debugging, and maintaining the PixelCraft Bloom system in development and production environments.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Docker Compose Workflow](#docker-compose-workflow)
4. [Testing and Validation](#testing-and-validation)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)
7. [Performance and Optimization](#performance-and-optimization)

---

## Quick Start

### 5-Minute Setup (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/codesleeps/pixelcraft-bloom.git
cd pixelcraft-bloom

# 2. Install Ollama (if not already installed)
# Visit https://ollama.ai and download for your OS

# 3. Start Ollama in a new terminal
ollama serve

# 4. In another terminal, pull the required model
ollama pull mistral        # Fast, stable, Docker-compatible

# 5. Install and run backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env if needed (default localhost:11434 should work)
uvicorn app.main:app --reload

# 6. In another terminal, start frontend
cd ..  # Back to root
npm install
npm run dev

# 7. Open http://localhost:5173 in your browser
```

### 5-Minute Setup (Docker Compose)

```bash
# 1. Ensure Docker Desktop is running with 12GB+ memory allocated

# 2. Clone and navigate
git clone https://github.com/codesleeps/pixelcraft-bloom.git
cd pixelcraft-bloom

# 3. Start all services
docker compose up -d

# 4. Wait for Ollama to initialize (mistral model only, ~5GB)
docker compose logs -f ollama | grep -E "success|listening"

# 5. Test the API
curl http://localhost:8000/api/models | jq .
# Should show "mistral" in the models list

# 6. Open http://localhost:5173 in your browser
```

**Note**: Docker Compose uses `mistral` (7B, stable) by default. For advanced tasks requiring `mixtral:8x7b`, set up local Ollama on the host (requires 24GB+ RAM). See [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md).

---

## Local Development

### Prerequisites

- **macOS/Linux/Windows**: Git, Docker (recommended)
- **macOS**: Ollama from https://ollama.ai
- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **8GB RAM minimum**: For local Ollama inference

### Step-by-Step Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/codesleeps/pixelcraft-bloom.git
cd pixelcraft-bloom
```

#### Step 2: Set Up Environment Files

```bash
# Backend environment
cp backend/.env.example backend/.env

# Optional: Edit backend/.env to customize settings
# Default values should work for local development
```

#### Step 3: Start Ollama Server

```bash
# In Terminal 1:
ollama serve

# Verify Ollama is running:
curl http://localhost:11434/api/tags
# Should return JSON with available models
```

#### Step 4: Pull Models

```bash
# In Terminal 2:
# Pull the primary model (required, Docker-compatible)
ollama pull mistral        # ~5GB, fast inference, stable for Docker Desktop

# Optional: For local development on high-end machines (requires 24GB+ RAM)
# ollama pull mixtral:8x7b   # ~26GB quantized, powerful but resource-intensive
```

#### Step 5: Start Backend

```bash
# In Terminal 3:
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

#### Step 6: Start Frontend

```bash
# In Terminal 4:
npm install
npm run dev

# You should see:
# VITE v4.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

#### Step 7: Verify Everything Works

```bash
# In Terminal 5, test the backend API:
curl http://localhost:8000/api/models | jq .

# Expected output:
# {
#   "models": [
#     {
#       "name": "mistral",
#       "provider": "ollama",
#       "health": true,
#       "metrics": {}
#     }
#   ]
# }

# Test chat endpoint:
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Say hello"}'

# Expected: Model-generated response (not fallback message)
```

### Daily Development Workflow

**Morning (Start of Day)**:
```bash
# Terminal 1: Ensure Ollama is running
ollama serve

# Terminal 2: Check model status
curl http://localhost:11434/api/tags | jq '.models[0].name'

# Terminal 3: Start backend
cd pixelcraft-bloom/backend
uvicorn app.main:app --reload

# Terminal 4: Start frontend
cd pixelcraft-bloom
npm run dev
```

**During Development**:
- Edit frontend files in `src/` - Vite auto-reloads
- Edit backend files in `backend/app/` - Uvicorn auto-reloads (with `--reload`)
- Check browser console for errors
- Check backend terminal for error messages

**End of Day**:
```bash
# Stop services (Ctrl+C in each terminal)
# OR kill all at once:
pkill ollama
pkill uvicorn
pkill vite
```

---

## Docker Compose Workflow

### Setup (One Time)

```bash
# 1. Navigate to repository root
cd pixelcraft-bloom

# 2. Ensure Docker Desktop has 12GB+ memory allocated
# Open Docker → Preferences → Resources → Memory

# 3. Create .env file (if not exists)
cp backend/.env.example .env

# 4. Start services
docker compose up -d

# 5. Wait for services to be ready
docker compose logs -f | grep "ready\|listening\|started"
# Takes 30-60 seconds on first run (Ollama pulls model)
```

### Daily Workflow

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# Follow all logs
docker compose logs -f

# Or specific service logs:
docker compose logs -f backend
docker compose logs -f ollama
docker compose logs -f postgres

# Stop all services
docker compose down

# Stop and remove data (fresh start)
docker compose down -v
```

### Rebuilding Services

```bash
# After changing backend code/dependencies:
docker compose build backend
docker compose up -d backend

# After changing docker-compose.yml or .env:
docker compose down
docker compose up -d

# After Ollama changes (model additions):
docker compose restart ollama
docker compose logs -f ollama  # Watch for model pulling
```

### Common Docker Compose Issues

```bash
# Port already in use
# Change port in docker-compose.yml and restart:
# ports:
#   - "8001:8000"  # Use different host port
docker compose restart

# Service won't start
docker compose logs <service-name>  # Check error messages
docker compose restart <service-name>

# Need clean state
docker compose down -v
docker compose up -d

# Memory issues
# Increase Docker memory in Docker Desktop preferences to 16GB
# Or reduce Ollama memory limit in docker-compose.yml
```

---

## Testing and Validation

### Unit Tests (Backend)

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=app --cov-report=html
# View report: open htmlcov/index.html

# Run specific test
pytest tests/test_models.py::test_model_manager_initialization -v
```

### Integration Tests

```bash
# Requires backend running (either locally or in Docker)

# Test all endpoints
cd backend
pytest tests/test_api.py -v

# Test Ollama integration specifically
pytest tests/test_ollama_integration.py -v
```

### Manual API Testing

```bash
# Get available models
curl http://localhost:8000/api/models | jq .

# Chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?"}'

# Health check
curl http://localhost:8000/health | jq .

# Backend info
curl http://localhost:8000/info | jq .
```

### Frontend Tests

```bash
# Run frontend tests
npm test

# Watch mode (reruns on file changes)
npm test -- --watch

# Coverage report
npm test -- --coverage
```

### Smoke Test Script

A comprehensive smoke test suite is provided in `scripts/smoke-test.sh`. This script validates core system functionality with retry logic and timeout handling.

**Features:**
- 4 test cases: Health check, Models list, Chat message, Model details
- 3 retry attempts per endpoint with exponential backoff
- JSON validation using `jq`
- Colored output (GREEN ✓, RED ✗, YELLOW for retries)
- Exit codes for CI/CD integration

**Run the tests:**

```bash
chmod +x scripts/smoke-test.sh
./scripts/smoke-test.sh
```

**Expected output (with current Docker Desktop setup):**

```
Health Check... ✓ PASS
Models List... ✓ PASS
Chat Message... retry(1/3)... retry(2/3)... ✗ FAIL
Model Details... ✓ PASS

Results: Passed: 3, Failed: 1
```

**Known Limitation - Chat Endpoint Timeout:**

The chat endpoint may timeout due to Ollama infrastructure constraints on Docker Desktop (resource limitations, model loader timeouts). This is a **known issue**, not an application defect. See [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md) for details.

When this occurs:
- Health check and models listing work reliably ✓
- Chat inference may timeout or return a fallback message
- Retrying after several seconds often succeeds once the model is loaded
- Production deployments with dedicated Ollama resources will perform better

**For CI/CD:**

```bash
# Exit code 0 = all tests pass (≥3/4 tests)
# Exit code 1 = tests fail (<3/4 tests)
if ./scripts/smoke-test.sh; then
  echo "Smoke tests passed"
else
  echo "Smoke tests failed - review logs"
  exit 1
fi
```

---

## Common Tasks

### Adding a New Model

**Local Development**:
```bash
# Pull new model
ollama pull llama3:latest

# Update backend config
# Edit backend/app/models/config.py:
# MODELS = {
#     "mistral": ...,
#     "llama3": ModelConfig(name="llama3", provider="ollama", ...),
# }

# Update priorities if needed
# MODEL_PRIORITIES["chat"] = ["llama3", "mistral"]

# Restart backend
# (Uvicorn with --reload will detect changes)
```

**Docker Compose**:
```bash
# Update docker-compose.yml Ollama service to pull new model:
# ollama:
#   environment:
#     - OLLAMA_MODELS="mistral llama3"

# Or manually pull after starting:
docker exec pixelcraft-bloom-ollama-1 ollama pull llama3

# Restart backend to register new model
docker compose restart backend
```

### Updating Environment Variables

**Local Development**:
```bash
# Edit backend/.env
vim backend/.env

# Restart backend (Uvicorn will reload on file changes)
# OR manually restart if needed
```

**Docker Compose**:
```bash
# Edit .env file in repository root
vim .env

# Restart services
docker compose restart

# Or rebuild and restart:
docker compose down
docker compose up -d
```

### Checking Logs

**Local Development**:
```bash
# Backend logs (Uvicorn terminal)
# Frontend logs (npm run dev terminal)
# Ollama logs (ollama serve terminal)

# To grep for errors:
# In each terminal, search output or redirect to file:
# uvicorn app.main:app --reload 2>&1 | tee backend.log
# grep ERROR backend.log
```

**Docker Compose**:
```bash
# All logs with timestamp
docker compose logs --timestamps

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail 100 backend

# Search logs
docker compose logs | grep -i error

# Export logs to file
docker compose logs > logs.txt
```

### Restarting Services

**Local Development**:
```bash
# Automatic: Most services auto-reload on file changes
# Manual: Ctrl+C in terminal and restart

# Restart Ollama
# Ctrl+C in ollama serve terminal
# Run: ollama serve
```

**Docker Compose**:
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend

# Restart and rebuild
docker compose build backend && docker compose up -d backend
```

### Clearing Cache/State

**Local Development**:
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Clear npm cache (optional)
npm cache clean --force

# Restart services for clean state
```

**Docker Compose**:
```bash
# Stop and remove containers and volumes (clean slate)
docker compose down -v

# Start fresh
docker compose up -d

# Takes 30-60 seconds for model to pull
```

---

## Troubleshooting

### Problem: Chat Endpoint Returns Fallback Message

**Symptom**: `/api/models` shows model as healthy=true, but `/api/chat/message` returns "I'm sorry, I'm currently unable to..."

**Diagnosis**:
```bash
# 1. Check if Ollama is running and model exists
curl http://localhost:11434/api/tags | jq .

# 2. Check backend logs for timeout errors
docker compose logs backend | grep -i timeout

# 3. Check Ollama logs
docker compose logs ollama | tail -20
```

**Solution** (in order):

1. **Wait longer for first request** (most common)
   - First inference request loads model runner (can take 30+ seconds)
   - Retry the request after waiting

2. **Increase timeout in backend**
   - Edit `backend/app/config.py`
   - Increase `OllamaConfig.timeout` from 300 to 600
   - Restart backend

3. **Check Docker memory**
   - Docker Desktop → Preferences → Resources → Memory
   - Increase to 12GB+ if set lower
   - Restart Docker

4. **Check Ollama logs for actual errors**
   ```bash
   docker compose logs ollama | grep -i error
   ```

### Problem: Ollama Container Won't Start

**Symptom**: `docker compose logs ollama` shows errors

**Diagnosis**:
```bash
docker compose logs ollama
```

**Common Solutions**:

1. **Insufficient memory** → Increase Docker memory to 12GB
2. **Port conflict** → Change port in docker-compose.yml
3. **Model download failed** → Check network connectivity
4. **Disk space** → Ensure 20GB+ free space

### Problem: Backend API Not Responding

**Symptom**: `curl http://localhost:8000/api/models` times out or refuses connection

**Diagnosis**:
```bash
# Check if backend is running
docker compose ps backend

# Check backend logs
docker compose logs backend

# Check port is open
netstat -an | grep 8000
# or: lsof -i :8000
```

**Solutions**:

1. **Backend not started**: `docker compose up -d backend`
2. **Port in use**: Kill process on port 8000 or change port in compose file
3. **Backend crashed**: Check logs for errors: `docker compose logs backend`
4. **Network issue**: Ensure services can communicate

### Problem: Out of Memory Errors

**Symptom**: Backend/Ollama processes killed; `docker stats` shows high memory

**Solutions**:

1. **Increase Docker memory**:
   - Open Docker Desktop preferences
   - Resources → Memory → Set to 16GB+
   - Restart Docker

2. **Reduce Ollama memory limit**:
   - Edit `docker-compose.yml` Ollama service
   - Set `memory: 8G` instead of 12G
   - Restart

3. **Use smaller model**:
   - Replace `mistral` (5GB) with `phi` (2.7GB)
   - Edit `.env`: `OLLAMA_MODEL=phi`
   - Pull model: `docker exec pixelcraft-bloom-ollama-1 ollama pull phi`

4. **Monitor resource usage**:
   ```bash
   docker stats
   # Shows memory/CPU for each container
   ```

### Problem: Frontend Shows Blank Page

**Symptom**: Browser shows white screen; nothing loads

**Diagnosis**:
```bash
# 1. Check browser console (F12 → Console)
# Look for JavaScript errors

# 2. Check frontend logs
# npm run dev terminal should show compilation errors

# 3. Check network requests (F12 → Network)
# Verify API calls to backend are succeeding

# 4. Check if Vite dev server is running
curl http://localhost:5173
```

**Solutions**:

1. **Rebuild frontend**:
   ```bash
   cd pixelcraft-bloom
   npm install
   npm run dev
   ```

2. **Check backend connectivity**:
   ```bash
   # Verify backend is accessible from frontend
   curl http://localhost:8000/api/models
   ```

3. **Clear browser cache**:
   - Hard refresh: Cmd+Shift+R (macOS) or Ctrl+Shift+R (Linux/Windows)
   - Open DevTools → Settings → Network → Disable cache

4. **Check environment variables**:
   - Verify `VITE_API_BASE_URL` in `.env` or window config
   - Should point to backend URL

### Problem: Slow Model Responses

**Symptom**: Chat responses take 30+ seconds; system feels sluggish

**Diagnosis**:
```bash
# Check CPU/memory usage
docker stats

# Check if model is loaded
curl http://localhost:11434/api/ps | jq .

# Check system resources
# macOS: Activity Monitor
# Linux: top or htop
```

**Solutions** (in order of impact):

1. **First request always slow** (expected)
   - Model runner initialization: 30-120s first time
   - Subsequent requests: 1-5s
   - This is normal behavior

2. **Increase Docker memory** (macOS)
   - Docker Desktop → Preferences → Resources → Memory
   - Set to 16GB+

3. **Reduce keep-alive time**:
   - Edit `.env`: `OLLAMA_KEEP_ALIVE=5m`
   - Lower timeout = more frequent reloads
   - Trade-off: slower first request after idle time

4. **Use smaller/faster model**:
   - Current: `mistral` (7B)
   - Faster: `phi` (2.7B)
   - Or: `mistral:q4_0` (quantized)

5. **Upgrade system resources**:
   - Add more RAM to Docker allocation
   - Use GPU if available
   - Consider faster storage (SSD)

### Problem: Network Errors in Logs

**Symptom**: Backend logs show "Connection refused", "TimeoutError", or "Network error"

**Diagnosis**:
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check hostname resolution
docker exec pixelcraft-bloom-backend-1 ping ollama
# Should succeed (not show "Name does not resolve")

# Check backend config
docker compose exec backend env | grep OLLAMA
```

**Solutions**:

1. **Start Ollama service**:
   - Local dev: `ollama serve`
   - Docker: `docker compose up -d ollama`

2. **Fix hostname in backend config**:
   - Docker compose: use service name `ollama` (internal DNS)
   - Local dev: use `localhost` or `127.0.0.1`
   - Verify `.env` has correct `OLLAMA_HOST`

3. **Check Docker network**:
   ```bash
   # Verify services are on same network
   docker network ls
   docker inspect pixelcraft-bloom_default
   # Should show both backend and ollama
   ```

4. **Restart services**:
   ```bash
   docker compose restart
   # Gives them time to reconnect
   ```

---

## Performance and Optimization

### Baseline Metrics

**Healthy system** (on 8GB Docker Desktop):

```
Endpoint: /api/models
Time: 100-200ms
Memory: Stable (~500MB)

Endpoint: /api/chat/message (first request)
Time: 30-120s (model loading)
Memory: Increases to 5GB+ (mistral model)

Endpoint: /api/chat/message (subsequent)
Time: 2-5s
Memory: Stable at 5GB+

Model keep-alive: 10 minutes
Response quality: Excellent (mistral 7B)
```

### Optimization Strategies

**For Speed**:
1. Use `phi` (2.7B) instead of mistral: 3x faster, slightly lower quality
2. Use quantized model: `mistral:q4_0` - 2x faster, minimal quality loss
3. Increase keep-alive: Model stays loaded, eliminates reload delays

**For Memory Efficiency**:
1. Reduce keep-alive: `OLLAMA_KEEP_ALIVE=5m` - Models unload sooner
2. Use smaller model: `phi` (2.7GB vs mistral 5GB)
3. Disable streaming: Simpler, less overhead

**For Scalability** (production):
1. Use 24GB+ Docker memory for multiple models
2. Implement model queue/scheduling (custom code)
3. Consider GPU acceleration (requires specific hardware)
4. Use load balancer (nginx) with multiple backend instances

### Monitoring Commands

```bash
# Real-time resource monitoring
docker stats

# Model status
curl http://localhost:11434/api/ps | jq .

# Backend health
curl http://localhost:8000/health | jq .

# Database connections (if using Postgres)
docker exec pixelcraft-bloom-postgres-1 \
  psql -U postgres -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Redis info (if using Redis)
docker exec pixelcraft-bloom-redis-1 redis-cli info stats
```

### Capacity Planning

**Single model (mistral)**:
- Peak memory: 6GB
- Recommended Docker allocation: 8-12GB
- Suitable for: Solo development, demos, low-traffic

**Multiple models**:
- Peak memory: 12-20GB (depending on models)
- Recommended Docker allocation: 24GB+
- Suitable for: Teams, production, high-traffic

**Scaling**:
- Horizontal: Deploy multiple backend instances behind load balancer
- Vertical: Add more CPU/memory to single instance
- Model serving: Dedicated Ollama server (separate from backend)

---

## Quick Reference

### Essential Commands

```bash
# LOCAL DEVELOPMENT
ollama serve                    # Start Ollama
ollama pull mistral            # Download model
uvicorn app.main:app --reload  # Start backend
npm run dev                     # Start frontend

# DOCKER COMPOSE
docker compose up -d            # Start all
docker compose down             # Stop all
docker compose logs -f          # Watch logs
docker compose restart          # Restart all
docker compose build backend    # Rebuild backend

# TESTING
curl http://localhost:8000/api/models
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi"}'

# DEBUGGING
docker compose logs backend | grep error
docker stats
docker exec pixelcraft-bloom-ollama-1 ollama list
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/.env` | Backend config |
| `docker-compose.yml` | Service definitions |
| `backend/app/models/config.py` | Model definitions |
| `backend/app/utils/ollama_client.py` | Ollama integration |
| `OLLAMA_SETUP_GUIDE.md` | Detailed Ollama docs |
| `README.md` | Project overview |

### Emergency Procedures

**System completely broken**:
```bash
docker compose down -v
docker compose up -d
# Wait 60s for Ollama to start
curl http://localhost:8000/api/models
```

**Memory completely exhausted**:
```bash
docker compose restart ollama
# OR increase Docker memory allocation and restart Docker
```

**Need clean slate**:
```bash
docker compose down -v
rm -rf backend/app/__pycache__
docker compose up -d
```

---

## Getting Help

1. **Check logs first**: `docker compose logs`
2. **See OLLAMA_SETUP_GUIDE.md** for Ollama-specific issues
3. **Check README.md** for architecture overview
4. **Search GitHub issues**: https://github.com/codesleeps/pixelcraft-bloom/issues
5. **Review troubleshooting section** above

