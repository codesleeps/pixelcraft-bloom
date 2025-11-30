# Ollama Setup and Troubleshooting Guide

This guide provides comprehensive instructions for setting up and troubleshooting Ollama with PixelCraft Bloom, particularly for Docker-based deployments on macOS.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Development Setup](#development-setup)
4. [Docker Compose Setup](#docker-compose-setup)
5. [Known Issues and Solutions](#known-issues-and-solutions)
6. [Performance Tuning](#performance-tuning)
7. [Advanced Configuration](#advanced-configuration)
8. [Monitoring and Debugging](#monitoring-and-debugging)

---

## Quick Start

### Local Development (macOS/Linux/Windows)

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Start Ollama server
ollama serve

# 3. In another terminal, pull the recommended model
ollama pull mistral

# 4. Verify installation
curl http://localhost:11434/api/tags

# 5. Run the backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set: OLLAMA_HOST=http://localhost:11434
uvicorn app.main:app --reload
```

### Docker Compose Setup

```bash
# 1. Start all services (Postgres, Redis, Ollama, Backend)
docker compose up -d

# 2. Wait for Ollama to pull the model (30-60 seconds on first run)
sleep 30

# 3. Test the chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, say this back: Hello"}'

# 4. View logs if needed
docker compose logs -f backend
docker compose logs -f ollama
```

---

## Architecture Overview

### Service Connectivity

In Docker Compose:

```
Frontend (React)
    ↓ (HTTP/WS)
Backend (FastAPI, port 8000)
    ↓ (HTTP to internal service name)
Ollama (internal: http://ollama:11434)
```

**Key Point**: Inside Docker containers, services communicate by their service name (`ollama`), not `localhost`. This is handled automatically by Docker's internal DNS.

### Model Lifecycle

```
1. Model Listed (/api/tags)          ← Health check uses this
   └─ Model shows in available models

2. First Inference Request
   └─ Ollama loads model into memory (30-120s depending on model size)
   └─ Model runner initializes
   └─ Response generated

3. Subsequent Requests
   └─ Model already loaded
   └─ Faster response times
```

**Problem**: If a request timeout occurs during step 2, the model may not be fully initialized. Subsequent retries should work once the model is loaded.

---

## Development Setup

### Prerequisites

- **Python 3.11+**
- **Ollama** (from https://ollama.ai)
- **Docker** (optional, for containerized setup)

### Step-by-Step Setup

#### 1. Install Ollama

Download and install from [ollama.ai](https://ollama.ai) following platform-specific instructions.

#### 2. Start Ollama Server

```bash
ollama serve
# Server runs on http://localhost:11434
```

#### 3. Pull Models

For development, we recommend **mistral** as the primary model:

```bash
# Primary model for all tasks (7B, fast, ~5GB)
ollama pull mistral

# Optional additional models (only if you have 16GB+ RAM)
# ollama pull llama2              # 7B general purpose
# ollama pull llama3.1:8b         # 8B advanced reasoning
# ollama pull codellama           # 7B code generation
```

**Why only Mistral for development?**

On resource-constrained systems (Docker Desktop on macOS):
- Loading multiple models simultaneously causes slow startup
- Model runner initialization can take 30+ seconds per model
- Memory contention leads to timeout errors
- A single well-configured model provides stable development

#### 4. Verify Installation

```bash
# Check running models
curl http://localhost:11434/api/tags | jq .

# Test inference
curl http://localhost:11434/api/generate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "prompt": "Hello", "stream": false}' | jq .
```

#### 5. Set Up Backend Environment

```bash
cd backend
cp .env.example .env

# Edit .env and set:
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_STREAM=false
OLLAMA_TIMEOUT=300
```

#### 6. Run Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 7. Test API Endpoints

```bash
# Get available models
curl http://localhost:8000/api/models | jq .

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Say hello in one sentence"}'
```

---

## Docker Compose Setup

### Configuration Details

The included `docker-compose.yml` provides a complete local development stack:

```yaml
services:
  postgres:          # PostgreSQL database
  redis:             # Redis cache
  ollama:            # Ollama model server
  backend:           # FastAPI backend
```

### Memory Requirements

**Minimum**: 8GB allocated to Docker  
**Recommended**: 12GB for comfortable development

#### macOS Docker Desktop Settings

1. Open Docker Desktop → Preferences
2. Go to Resources → Memory
3. Set to **12GB** or higher
4. Restart Docker

### Running the Stack

```bash
# Start all services
docker compose up -d

# View status
docker compose ps

# Follow backend logs
docker compose logs -f backend

# Follow Ollama logs (model pulling/loading)
docker compose logs -f ollama

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

### Waiting for Ollama to be Ready

Ollama pulls models on first run (5-15 minutes for mistral). Monitor with:

```bash
# Option 1: Watch Ollama logs
docker compose logs -f ollama | grep -i "pull\|load\|complete"

# Option 2: Poll health endpoint
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for Ollama..."
  sleep 5
done
echo "Ollama is ready!"

# Option 3: Check Docker stats
docker stats ollama  # Watch memory/CPU usage
```

### Rebuilding After Configuration Changes

```bash
# Rebuild backend image with new requirements/code
docker compose build backend

# Restart services
docker compose restart
```

---

## Known Issues and Solutions

### Issue 1: Chat Endpoint Returns Fallback Response

**Symptom**:
```
GET /api/models → {"models": [{"name": "mistral", "health": true}]}  ✓
POST /api/chat/message → "I'm sorry, I'm currently unable to process..."  ✗
```

**Root Cause**: Model health check (which calls `/api/tags`) succeeds, but actual inference request times out because model runner is still initializing.

**Solutions** (in order of preference):

1. **Wait longer after first request**
   - Health check is not a guarantee of inference readiness
   - First request to mistral can take 30-120s
   - Set retry timeout to 300s in config: `OLLAMA_TIMEOUT=300`

2. **Pre-warm model at startup**
   - Backend includes warm-up logic in `app/models/manager.py`
   - Check backend logs: `"Warming up model mistral..."`
   - If warm-up times out, it's logged but doesn't block startup

3. **Check Docker memory allocation**
   - Insufficient memory causes slow model loading
   - Increase Docker memory to 12GB+
   - Monitor: `docker stats ollama`

4. **Increase client-side timeout**
   - Edit `backend/app/config.py`:
     ```python
     class OllamaConfig:
         timeout = 300  # Increase from default
     ```
   - Restart backend: `docker compose restart backend`

### Issue 2: Ollama Container Uses Excessive Memory

**Symptom**: `docker stats ollama` shows 80%+ memory usage; system becomes slow

**Solutions**:

1. **Reduce Ollama memory allocation**
   - Edit `docker-compose.yml`:
     ```yaml
     ollama:
       deploy:
         resources:
           limits:
             memory: 8G  # Reduce from 12G
     ```
   - Restart: `docker compose restart ollama`

2. **Use a smaller model**
   - Current: `mistral` (7B, ~5GB RAM)
   - Alternatives: `phi` (2.7B), `neural-chat` (7B, more optimized)
   - Pull and test: `ollama pull phi`
   - Switch in `.env`: `OLLAMA_MODEL=phi`

3. **Add swap space** (advanced)
   - Allow Ollama to overflow to disk (slower but prevents OOM)
   - May help on resource-constrained systems

### Issue 3: Backend Service Crashes on Startup

**Symptom**: `docker compose logs backend` shows errors

**Common Causes**:

1. **Ollama not ready yet**
   - Ollama takes 30-60s to start and pull model
   - Add startup delay in docker-compose.yml:
     ```yaml
     backend:
       depends_on:
         ollama:
           condition: service_healthy  # Requires healthcheck in ollama service
     ```
   - OR manually wait: `sleep 60 && docker compose restart backend`

2. **Port 8000 already in use**
   - Check: `lsof -i :8000`
   - Kill process or use different port:
     ```yaml
     backend:
       ports:
         - "8001:8000"  # Use 8001 instead
     ```

3. **Environment variables missing**
   - Ensure `.env` file exists and has required vars
   - Test: `docker compose config | grep OLLAMA_`

### Issue 4: Timeouts During Model Pulling

**Symptom**: `docker compose logs ollama` shows repeated pull failures

**Solutions**:

1. **Pre-pull model before starting compose**
   ```bash
   # If Ollama is installed locally
   ollama pull mistral
   
   # Then start Docker Compose (model will already be available)
   docker compose up -d
   ```

2. **Increase pull timeout in docker-compose.yml**
   ```yaml
   ollama:
     environment:
       - OLLAMA_DOWNLOAD_TIMEOUT=3600  # 1 hour
   ```

3. **Check network connectivity**
   - Ensure Docker can reach ollama.ai CDN
   - Test: `docker exec -it ollama-container curl https://registry.ollama.ai/v2/`

### Issue 5: Mixtral:8x7b Llama Runner Crashes (OOM on Docker Desktop)

**Symptom**: `docker compose logs ollama` shows `"llama runner process has terminated: signal: killed"` after attempting mixtral:8x7b inference

**Cause**: **mixtral:8x7b is a 46.7B parameter model (26GB quantized) that requires ~25GB RAM just to load on CPU**. Docker Desktop on macOS with typical 12GB memory allocation cannot support this model for inference.

**Solutions**:

1. **Use `mistral` (7B, 5GB) instead — recommended for Docker Desktop**
   - Fully compatible with 12GB Docker memory limit
   - ModelManager will use `mistral` for fallback tasks
   - All inference endpoints work reliably
   - In docker-compose.yml or `.env`: keep default `OLLAMA_MODEL=mistral`

2. **Use mixtral:8x7b on host Ollama (not in Docker)**
   ```bash
   # Pull on host
   ollama pull mixtral:8x7b
   
   # Point backend to host Ollama
   # In .env: OLLAMA_HOST=http://host.docker.internal:11434  (macOS)
   # OR: OLLAMA_HOST=http://172.17.0.1:11434  (Linux)
   
   # Requires: Host Ollama running (`ollama serve`)
   # Requires: 32GB+ system RAM, or 24GB swap space
   ```

3. **Allocate more Docker Desktop memory (advanced)**
   - Docker Desktop → Preferences → Resources → Memory: set to 20GB+
   - Note: System may become unresponsive if you exceed available RAM
   - Not recommended on typical development machines

4. **Use GPU acceleration (advanced)**
   - Enable Metal (macOS) or CUDA (Linux): `OLLAMA_METAL=1` or `OLLAMA_CUDA_VISIBLE_DEVICES=0`
   - Requires compatible GPU (M1/M2/M3 macOS, NVIDIA CUDA on Linux)
   - Significantly reduces memory footprint (10-15GB for mixtral on GPU)

**Best Practice**: Keep `mistral` (5GB) as primary in Docker, use `mixtral:8x7b` locally on host if available for advanced tasks.

### Issue 6: Curl Errors (exit code 56, partial response)

**Symptom**: `curl` commands fail with network read errors

**Cause**: Model is timing out mid-response (usually during streaming)

**Solutions**:

1. **Disable streaming**
   - In `.env`: `OLLAMA_STREAM=false`
   - In `backend/app/models/config.py`: `supports_streaming=False`
   - Restart backend

2. **Increase curl timeout**
   ```bash
   curl --max-time 300 http://localhost:8000/api/models
   ```

3. **Check Ollama logs for errors**
   ```bash
   docker compose logs ollama | tail -50 | grep -i error
   ```

---

## Performance Tuning

### Model Selection Trade-Offs

| Model | Size | Speed | Quality | Memory | Notes |
|-------|------|-------|---------|--------|-------|
| **phi** | 2.7B | Fast | Good | 2GB | Best for constrained systems |
| **mistral** | 7B | Medium | Excellent | 5GB | **Recommended for dev** |
| **llama2** | 7B | Medium | Good | 5GB | General purpose |
| **llama3.1** | 8B | Medium | Excellent | 6GB | Advanced reasoning |
| **codellama** | 7B | Medium | Excellent (code) | 5GB | Code generation specialist |
| **mixtral** | 46B | Slow | Excellent | 26GB | Large system only |

### Optimization Tips

1. **Increase Keep-Alive Duration**
   ```
   OLLAMA_KEEP_ALIVE=30m  # Keep loaded models in memory longer
   ```
   - Prevents reload on subsequent requests
   - Trade-off: Uses more RAM

2. **Reduce Keep-Alive for Tight Memory**
   ```
   OLLAMA_KEEP_ALIVE=5m  # Unload model after 5 min of inactivity
   ```
   - Frees memory but slows first request after pause

3. **Monitor Model Loading**
   ```bash
   docker exec -it pixelcraft-bloom-ollama-1 ollama list
   ```

4. **Use Quantized Models**
   - Some models have quantized versions: `mistral:q4_0` (4-bit quantized)
   - Much faster but slightly lower quality
   - Test: `ollama pull mistral:q4_0`

---

## Advanced Configuration

### Custom Ollama Container Configuration

Edit `docker-compose.yml` Ollama service:

```yaml
ollama:
  image: ollama/ollama:latest
  container_name: pixelcraft-bloom-ollama
  ports:
    - "11435:11434"
  environment:
    - OLLAMA_HOST=0.0.0.0:11434
    - OLLAMA_KEEP_ALIVE=10m
    - OLLAMA_NUM_PARALLEL=1  # Process one request at a time
    - OLLAMA_NUM_THREADS=4   # CPU threads for inference
  volumes:
    - ollama_data:/root/.ollama  # Persist downloaded models
  deploy:
    resources:
      limits:
        memory: 12G
      reservations:
        memory: 8G
```

### Multiple Models in Production

To use multiple models (requires 24GB+ memory):

1. **Update `backend/app/models/config.py`**:
   ```python
   MODELS = {
       "mistral": ModelConfig(...),
       "llama3": ModelConfig(...),
       "codellama": ModelConfig(...),
   }
   ```

2. **Update `MODEL_PRIORITIES`**:
   ```python
   MODEL_PRIORITIES = {
       "chat": ["mistral", "llama3"],
       "code": ["codellama", "mistral"],
       # ... other task types
   }
   ```

3. **Pull models in Ollama container startup**:
   ```yaml
   ollama:
     entrypoint: ["bash", "-c"]
     command:
       - |
         ollama serve &
         sleep 10
         ollama pull mistral
         ollama pull llama3
         ollama pull codellama
         wait
   ```

4. **Increase Docker memory to 24GB+**

### Using Local Ollama with Docker Backend

If Ollama is already running on your host machine:

1. **macOS**: Change `docker-compose.yml`:
   ```yaml
   backend:
     environment:
       OLLAMA_HOST: http://host.docker.internal:11434  # macOS special DNS
   ```

2. **Linux**: Use bridge network or IP:
   ```yaml
   backend:
     environment:
       OLLAMA_HOST: http://172.17.0.1:11434  # Docker bridge gateway
   ```

3. **Remove Ollama service** from `docker-compose.yml` (optional)

---

## Monitoring and Debugging

### Checking Model Status

```bash
# List available models
curl http://localhost:11434/api/tags | jq .

# Check model metadata
curl http://localhost:11434/api/show -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "mistral"}' | jq .

# List running models
curl http://localhost:11434/api/ps | jq .
```

### Backend API Health Check

```bash
# Get models and their health status
curl http://localhost:8000/api/models | jq .

# Response example:
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

# If health is false, check backend logs:
docker compose logs backend | grep -i "error\|mistral\|timeout"
```

### Performance Monitoring

```bash
# Monitor Docker resource usage
docker stats pixelcraft-bloom-ollama-1

# Check backend response times
curl -w "Time taken: %{time_total}s\n" http://localhost:8000/api/models

# Monitor Ollama internally
docker exec pixelcraft-bloom-ollama-1 ps aux | grep ollama
```

### Enabling Debug Logging

1. **Backend debug logs**:
   ```bash
   # Add to docker-compose.yml backend service:
   environment:
     LOG_LEVEL: DEBUG  # More verbose logging
   ```

2. **View detailed logs**:
   ```bash
   docker compose logs -f backend | grep -i "ollama\|timeout\|error"
   ```

### Common Log Patterns

**Healthy startup**:
```
[INFO] Warming up model mistral...
[INFO] Model mistral warmed up successfully
[INFO] Server started on 0.0.0.0:8000
```

**Model timeout** (indicates slow loading):
```
[ERROR] TimeoutError: POST /api/chat timed out after 300s
[ERROR] Model mistral inference failed: TimeoutError
```

**Ollama not ready**:
```
[ERROR] Connection refused: http://ollama:11434
[ERROR] Cannot pull model: network unreachable
```

---

## Next Steps

### For Local Development

1. Follow [Development Setup](#development-setup)
2. Run `ollama serve` in a separate terminal
3. Start backend: `uvicorn app.main:app --reload`
4. Frontend runs with `npm run dev`
5. Test endpoints as shown above

### For Docker Compose Development

1. Follow [Docker Compose Setup](#docker-compose-setup)
2. Wait for Ollama to pull model
3. Test endpoints via curl or Postman
4. View logs to debug any issues

### For Production

1. Use a larger machine (24GB+ RAM)
2. Configure multiple models if needed
3. Set up monitoring and alerting
4. Consider GPU acceleration if available
5. See main [README.md](README.md) for deployment options

### Getting Help

- Check [Known Issues](#known-issues-and-solutions) section first
- Review backend logs: `docker compose logs -f backend`
- Check Ollama logs: `docker compose logs -f ollama`
- Verify Ollama directly: `curl http://localhost:11434/api/tags`
- Ensure `.env` has correct `OLLAMA_HOST` value

---

## Related Files

- `backend/.env.example` - Environment configuration template
- `backend/app/models/config.py` - Model definitions and priorities
- `backend/app/utils/ollama_client.py` - Ollama API client with retries
- `backend/app/models/manager.py` - Model selection and health checking
- `docker-compose.yml` - Local development stack definition
- `backend/Dockerfile` - Backend image definition

