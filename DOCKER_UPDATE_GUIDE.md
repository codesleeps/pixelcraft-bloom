# Docker Update Guide

**Date**: December 8, 2024  
**Purpose**: Update Docker images to match local code changes

---

## Changes Made to Local Files

The following files have been updated and need to be reflected in Docker images:

### 1. **backend/app/config.py**
- Added `model_config = {"env_nested_delimiter": "__"}` to AppConfig
- Enables proper parsing of nested configuration with double underscores

### 2. **backend/app/routes/models.py**
- Added `GET /api/models` endpoint
- Added `GET /api/models/{model_name}` endpoint
- Enhanced API documentation with comprehensive docstrings

### 3. **backend/app/routes/websocket.py**
- Fixed websocket decorator (removed invalid `summary` parameter)
- Added proper docstring for analytics websocket

### 4. **backend/.env**
- Updated to use double underscore notation for nested config
- Added proper Supabase and Redis configuration

---

## How to Update Docker Images

### Step 1: Start Docker Desktop

```bash
# On macOS
open -a Docker

# Wait for Docker to start (check the menu bar icon)
```

### Step 2: Rebuild Backend Image

```bash
# Rebuild the backend image with latest code
docker compose build backend

# Or rebuild all images
docker compose build
```

**Expected Output**:
```
[+] Building 45.2s (18/18) FINISHED
 => [backend internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.23kB
 => [backend internal] load .dockerignore
 => [backend internal] load metadata for docker.io/library/python:3.11-slim
 ...
 => [backend] exporting to image
 => => exporting layers
 => => writing image sha256:...
 => => naming to docker.io/library/agentsflowai-backend:dev
```

### Step 3: Stop Running Containers

```bash
# Stop all services
docker compose down

# Or stop and remove volumes for a fresh start
docker compose down -v
```

### Step 4: Update Environment Variables

Ensure your `.env` file in the project root has the correct configuration:

```bash
# Check if .env exists
ls -la .env

# If not, copy from backend
cp backend/.env .env
```

**Required variables in `.env`**:
```bash
# Supabase (with double underscores for nested config)
SUPABASE__URL=https://jufpxjbxakvjluezegbz.supabase.co
SUPABASE__KEY=your-service-role-key
SUPABASE__JWT_SECRET=your-jwt-secret

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama (use Docker service name)
OLLAMA_HOST=http://ollama:11434

# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3001,http://localhost:5173
```

### Step 5: Start Updated Services

```bash
# Start all services with updated images
docker compose up -d

# Watch logs to verify startup
docker compose logs -f backend
```

**Expected logs**:
```
backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
backend-1  | INFO:     Application startup complete.
backend-1  | INFO:     ModelManager initialized, available models: ['mistral', 'mixtral']
backend-1  | INFO:     Agents initialized successfully
```

### Step 6: Verify the Updates

```bash
# Test health endpoint
curl http://localhost:8000/health | jq .

# Test model endpoints (the new endpoints!)
curl http://localhost:8000/api/models | jq .

# Test specific model
curl http://localhost:8000/api/models/mistral | jq .
```

**Expected response for `/api/models`**:
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
        "capabilities": {
          "chat": true,
          "completion": true,
          "code_completion": true
        }
      }
    }
  ]
}
```

---

## Troubleshooting

### Issue: Docker daemon not running

**Error**: `Cannot connect to the Docker daemon`

**Solution**:
```bash
# Start Docker Desktop
open -a Docker

# Wait for it to start (check menu bar)
# Then retry the docker compose commands
```

### Issue: Build fails with dependency errors

**Error**: `ERROR: Could not find a version that satisfies the requirement...`

**Solution**:
```bash
# Clear Docker build cache
docker builder prune -a

# Rebuild without cache
docker compose build --no-cache backend
```

### Issue: Container starts but endpoints return 404

**Error**: `404 Not Found` for `/api/models`

**Solution**:
```bash
# Verify the image was rebuilt
docker images | grep agentsflowai-backend

# Check the build date (should be recent)
docker inspect agentsflowai-backend:dev | jq '.[0].Created'

# If old, force rebuild
docker compose build --no-cache backend
docker compose up -d --force-recreate backend
```

### Issue: Configuration errors on startup

**Error**: `ValidationError: Field required`

**Solution**:
```bash
# Check environment variables in container
docker compose exec backend env | grep SUPABASE

# Verify .env file has double underscores
cat .env | grep SUPABASE

# Should show:
# SUPABASE__URL=...
# SUPABASE__KEY=...
# SUPABASE__JWT_SECRET=...

# If not, update .env and restart
docker compose restart backend
```

### Issue: Ollama connection fails

**Error**: `Ollama connectivity: False`

**Solution**:
```bash
# Check if Ollama container is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Pull models into Ollama container
docker compose exec ollama ollama pull mistral:7b
docker compose exec ollama ollama pull mixtral:8x7b

# Verify models are available
docker compose exec ollama ollama list
```

---

## Quick Commands Reference

```bash
# Rebuild backend image
docker compose build backend

# Start all services
docker compose up -d

# Watch backend logs
docker compose logs -f backend

# Restart backend only
docker compose restart backend

# Stop all services
docker compose down

# Fresh start (removes volumes)
docker compose down -v && docker compose up -d

# Check running containers
docker compose ps

# Execute command in backend container
docker compose exec backend python -c "from app.config import settings; print(settings.supabase.url)"

# Test endpoints from host
curl http://localhost:8000/health
curl http://localhost:8000/api/models
```

---

## Verification Checklist

After updating Docker images, verify:

- [ ] Docker Desktop is running
- [ ] Backend image rebuilt successfully
- [ ] `.env` file has correct configuration (double underscores)
- [ ] All containers are running (`docker compose ps`)
- [ ] Backend logs show successful startup
- [ ] Health endpoint returns 200 (`curl http://localhost:8000/health`)
- [ ] Model endpoints return data (`curl http://localhost:8000/api/models`)
- [ ] Models show `"health": true` in response
- [ ] No errors in backend logs

---

## Production Deployment

For production deployment with updated images:

### 1. Build Production Images

```bash
# Build with production Dockerfile
docker compose -f docker-compose.prod.yml build

# Or build specific production image
docker build -f backend/Dockerfile.prod -t agentsflowai-backend:prod .
```

### 2. Tag and Push to Registry

```bash
# Tag for your registry
docker tag agentsflowai-backend:dev your-registry.com/agentsflowai-backend:latest

# Push to registry
docker push your-registry.com/agentsflowai-backend:latest
```

### 3. Deploy to Production

```bash
# Pull latest images on production server
docker compose -f docker-compose.prod.yml pull

# Restart services with new images
docker compose -f docker-compose.prod.yml up -d

# Verify deployment
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/api/models
```

---

## Summary

**To update Docker images with latest code changes:**

1. ✅ Start Docker Desktop
2. ✅ Run `docker compose build backend`
3. ✅ Update `.env` file with double underscore notation
4. ✅ Run `docker compose down && docker compose up -d`
5. ✅ Verify with `curl http://localhost:8000/api/models`

**Expected result**: Model endpoints working with `"health": true`

---

**Last Updated**: December 8, 2024  
**Status**: Ready for Docker image update
