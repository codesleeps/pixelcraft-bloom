# PixelCraft Bloom - Quick Reference Card

## Local Development (5 minutes)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull model (once)
ollama pull mistral

# Terminal 3: Start backend
cd backend && pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Terminal 4: Start frontend
npm install && npm run dev

# Terminal 5: Test
curl http://localhost:8000/api/models | jq .
```

**Access Points**:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Compose (3 commands)

```bash
# Start
docker compose up -d

# Monitor (wait 30-60 seconds for first run)
docker compose logs -f | grep "ready\|listening"

# Test
curl http://localhost:8000/api/models | jq .
```

**All Services**:
- Frontend (static): N/A (served by npm)
- API: http://localhost:8000
- Database: localhost:5432
- Redis: localhost:6379
- Ollama: http://localhost:11435 (port 11434 internally)

---

## Essential Commands

### Check Status
```bash
# Local: Check if Ollama is running
curl http://localhost:11434/api/tags | jq .

# Docker: Check all services
docker compose ps

# Docker: Watch logs
docker compose logs -f
```

### Restart Services
```bash
# Local: Ctrl+C in each terminal, then restart

# Docker: Restart one service
docker compose restart backend

# Docker: Restart all
docker compose down && docker compose up -d
```

### Test API
```bash
# Get models
curl http://localhost:8000/api/models | jq .

# Chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Say hello"}'
```

### View Logs
```bash
# Local: Watch terminal output directly

# Docker: All services
docker compose logs

# Docker: Specific service
docker compose logs -f backend

# Docker: Last N lines
docker compose logs --tail 50 backend

# Docker: Search for errors
docker compose logs | grep -i error
```

---

## Configuration

### Critical Variables (in `.env`)

```env
# Ollama
OLLAMA_HOST=http://localhost:11434          # Local dev
OLLAMA_HOST=http://ollama:11434             # Docker
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=300                          # seconds
OLLAMA_STREAM=false

# Database (Docker)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pixelcraft

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Model Selection (for advanced users)

**Supported Models** (for production):
- `mistral` (7B) - Current, recommended
- `phi` (2.7B) - Faster, less memory
- `llama2` (7B) - General purpose
- `llama3:8b` (8B) - Advanced reasoning
- `codellama` (7B) - Code generation

**Switch Model**:
```bash
# Local: Stop backend, edit backend/.env, restart
# Docker: Update .env, then:
docker compose restart backend
```

---

## Troubleshooting Quick Fixes

### Chat Returns Fallback Message
```bash
# Symptom: /api/models shows healthy=true, but /api/chat/message fails
# Cause: First request loading model runner (30-120s)
# Solution: Wait 60 seconds and retry

# Or check status:
docker compose logs ollama | tail -5
docker stats
```

### Services Won't Start
```bash
# Check what's blocking
docker compose logs

# Clean slate
docker compose down -v
docker compose up -d

# Wait 60 seconds (Ollama pulls model first time)
```

### Port Already in Use
```bash
# Find what's using port
lsof -i :8000   # Backend port
lsof -i :11434  # Ollama port

# Kill if needed
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Memory Issues
```bash
# Check memory usage
docker stats

# If Docker Desktop (macOS):
# Open Docker → Preferences → Resources → Memory
# Increase to 12GB+
# Restart Docker
```

### Network Errors
```bash
# Verify services can communicate
docker compose exec backend ping ollama
# Should succeed (not "Name does not resolve")

# If fails, restart services
docker compose restart
```

---

## File Locations

```
pixelcraft-bloom/
├── src/                      # React frontend
│   ├── App.tsx              # Main component
│   ├── index.css            # Styles
│   └── pages/               # Route components
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # App entry point
│   │   ├── config.py        # Settings
│   │   ├── models/          # Model configuration
│   │   ├── utils/           # Utilities
│   │   └── routes/          # API endpoints
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example         # Config template
│   └── Dockerfile           # Container definition
├── docker-compose.yml        # Multi-service setup
├── .env                      # Config (create from .env.example)
├── package.json             # JS dependencies
├── README.md                # Project overview
├── OLLAMA_SETUP_GUIDE.md    # Ollama details
├── RUNBOOK.md               # Operations guide
└── RELEASE_NOTES.md         # Version info
```

---

## Key Files for Developers

| File | Purpose | Edit When |
|------|---------|-----------|
| `.env` | Environment configuration | Changing Ollama host, ports, API keys |
| `backend/app/models/config.py` | Model definitions | Adding/removing models, changing task priorities |
| `backend/app/utils/ollama_client.py` | Ollama client logic | Adjusting timeout, retry logic, debugging |
| `docker-compose.yml` | Service definitions | Adding services, changing memory limits, ports |
| `src/App.tsx` | Frontend entry | Adding new pages, updating layout |

---

## Environment Setup Checklist

### Local Development
- [ ] Install Ollama (ollama.ai)
- [ ] Install Python 3.11+
- [ ] Install Node.js 18+
- [ ] Clone repository
- [ ] `ollama pull mistral`
- [ ] Create `backend/.env` from `.env.example`
- [ ] Start Ollama, backend, frontend (3 terminals)

### Docker Compose
- [ ] Docker Desktop running with 12GB+ memory
- [ ] Clone repository
- [ ] Create `.env` from `backend/.env.example`
- [ ] `docker compose up -d`
- [ ] Wait 30-60 seconds for services to start

---

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Ollama startup | 5-10s | First time pulls model (~30s total) |
| Health check | 100-200ms | Fast, just lists available models |
| First chat request | 30-120s | Model runner initialization (expected) |
| Subsequent chat | 2-5s | Model already loaded |
| Model switching | ~5s | Model unloads from memory after 10 min idle |

---

## Common Patterns

### Adding a New Environment Variable
```bash
# 1. Add to .env
echo "NEW_VAR=value" >> .env

# 2. Read in config
# backend/app/config.py:
# new_var = os.getenv("NEW_VAR", "default")

# 3. Restart backend
docker compose restart backend
```

### Testing an API Endpoint
```bash
# With curl
curl -X POST http://localhost:8000/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# With jq (pretty print)
curl http://localhost:8000/api/models | jq .

# With timeout
curl --max-time 10 http://localhost:8000/api/models
```

### Clearing Cache/Logs
```bash
# Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Docker containers (keep volumes)
docker compose restart

# Docker full clean (removes everything)
docker compose down -v
docker compose up -d
```

---

## Emergency Commands

```bash
# Everything broken? Fresh start
docker compose down -v && docker compose up -d

# Services hanging? Force restart
docker compose kill && docker compose up -d

# Memory exhausted? Restart Ollama
docker compose restart ollama

# Check what's using resources
docker stats

# See detailed errors
docker compose logs backend 2>&1 | grep -i error | tail -20

# Test connectivity between services
docker compose exec backend ping ollama
```

---

## Getting Help

1. **Check logs first**
   ```bash
   docker compose logs | grep -i error
   ```

2. **See documentation**
   - Setup: OLLAMA_SETUP_GUIDE.md
   - Operations: RUNBOOK.md
   - Versions: RELEASE_NOTES.md

3. **Specific issues**
   - Timeout/slow: See OLLAMA_SETUP_GUIDE.md "Known Issues"
   - Can't start: See RUNBOOK.md "Troubleshooting"
   - Configuration: See README.md "Environment Variables"

4. **GitHub Issues**
   - Search: https://github.com/codesleeps/pixelcraft-bloom/issues
   - Create: Include logs, Docker stats, steps to reproduce

---

## Useful Links

- **Ollama**: https://ollama.ai
- **FastAPI**: https://fastapi.tiangolo.com
- **React**: https://react.dev
- **Docker Compose**: https://docs.docker.com/compose
- **Project Repo**: https://github.com/codesleeps/pixelcraft-bloom

---

**Last Updated**: 2025-01-29  
**Current Version**: 1.1.0  
**Stable**: Yes (single mistral model configuration)

