# Production Readiness Checklist

This document outlines the remaining tasks required before launching the PixelCraft backend to production.

## 1. Environment Variable Validation on Startup
- Implement validation using **pydantic** `BaseSettings` or **python-dotenv**.
- Fail fast with clear error messages for missing or malformed variables.
- Example snippet (add to `backend/app/config.py`):
```python
from pydantic import BaseSettings, ValidationError, validator

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    # Add other required vars

    @validator("DATABASE_URL", "REDIS_URL")
    def ensure_url(cls, v):
        if not v.startswith("postgres://") and not v.startswith("redis://"):
            raise ValueError("Invalid URL format")
        return v

settings = Settings()
```

## 2. Database Connection Pooling Configuration
- Use **SQLAlchemy** with `pool_size` and `max_overflow` settings.
- For Supabase/PostgreSQL, configure PgBouncer or built‑in pooling.
- Example (add to `backend/app/database.py`):
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

## 3. Redis Connection Retry Logic
- Wrap Redis client creation in a retry loop (exponential backoff).
- Use **tenacity** library for clean implementation.
- Example:
```python
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_redis_client():
    return redis.from_url(settings.REDIS_URL)

redis_client = get_redis_client()
```

## 4. Rate Limiting Per User (Currently Global)
- Switch from a global limiter to a per‑user key in Redis.
- Example using **slowapi**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=lambda request: request.headers.get("X-User-Id", get_remote_address()))
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)
```
- Update routes with `@limiter.limit("100/minute")`.

## 5. API Documentation (Swagger/OpenAPI) – Add Descriptions
- FastAPI automatically generates OpenAPI, but many endpoints lack docstrings.
- Add `summary` and `description` parameters to route decorators and use Pydantic models with field docs.
- Example:
```python
@router.post("/chat", summary="Chat with AI", description="Send a user message and receive a streamed AI response.")
async def chat_endpoint(request: ChatRequest):
    ...
```
- Run `uvicorn` and verify at `/docs`.

## 6. Backup / Restore Procedures Documentation
- Create a `BACKUP_RESTORE.md` covering:
  - Daily automated Supabase dump (`pg_dump`).
  - Redis RDB/AOF backup strategy.
  - Script to restore both DB and cache.
  - Verification steps.
- Example placeholder:
```markdown
# Backup & Restore
## Database
```bash
pg_dump $DATABASE_URL > backups/$(date +%F).sql
```
## Redis
```bash
redis-cli --rdb backups/redis-$(date +%F).rdb
```
```

## 7. Load Testing Results & Capacity Planning
- Consolidate recent Locust results (already in `CAPACITY_PLANNING.md`).
- Add a summary table linking metrics to recommended limits.
- Reference this section from the capacity planning doc.

## 8. SSL Certificate Setup for Custom Domain
- Use **Let's Encrypt** with **certbot** (or Cloudflare SSL if hosted on Vercel).
- Steps:
  1. Obtain a domain and point DNS to server IP.
  2. Install certbot: `sudo apt-get install certbot`.
  3. Run: `sudo certbot --nginx -d yourdomain.com` (or `--standalone` for non‑nginx).
  4. Configure FastAPI behind a reverse proxy (nginx) to use `https://`.
  5. Set up automatic renewal (`certbot renew --dry-run`).

---
**Next Actions**
- Implement environment validation and DB pooling in codebase.
- Update rate limiting middleware.
- Add missing OpenAPI descriptions.
- Draft backup/restore scripts and add `BACKUP_RESTORE.md`.
- Configure SSL on staging before production rollout.

*All items above should be tracked in the project’s issue tracker (e.g., GitHub Projects) and marked as done before the launch date.*
