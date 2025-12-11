# AgentsFlowAI Performance Optimization Guide

This guide provides performance optimization strategies for AgentsFlowAI in production environments.

## 📊 Current Performance Baseline

Based on load testing results:
- **Chat API**: 50 req/sec sustained
- **Analytics API**: 25 req/sec (database-intensive)
- **WebSocket**: 100+ concurrent connections
- **Authentication**: <200ms response time

## 🚀 Immediate Optimizations

### 1. Database Query Optimization

**Add Indexes** for frequently queried columns:

```sql
-- Add these indexes to your Supabase database
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
```

**Optimize Slow Queries**:

```python
# In backend/app/utils/supabase_client.py

@cache(ttl=300)  # Cache for 5 minutes
async def get_user_conversations(user_id: str):
    """Get user conversations with caching"""
    query = """
    SELECT id, title, created_at, updated_at
    FROM conversations
    WHERE user_id = %s
    ORDER BY updated_at DESC
    LIMIT 50
    """
    return await database.fetch_all(query, user_id)
```

### 2. Redis Caching Strategy

**Implement Multi-Level Caching**:

```python
# In backend/app/utils/cache.py

from functools import wraps
import time
import hashlib

def multi_level_cache(ttl_short=60, ttl_long=300):
    """Multi-level caching decorator with short and long TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_base = f"{func.__module__}.{func.__name__}"
            key_hash = hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()
            cache_key = f"cache:{key_base}:{key_hash}"

            # Try short-term cache first
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return cached_data

            # Execute function if not in short-term cache
            result = await func(*args, **kwargs)

            # Store in short-term cache
            await redis_client.setex(cache_key, ttl_short, result)

            # Also store in long-term cache with different key
            long_cache_key = f"long_cache:{key_base}:{key_hash}"
            await redis_client.setex(long_cache_key, ttl_long, result)

            return result
        return wrapper
    return decorator
```

### 3. Connection Pooling Optimization

**Tune Database Connection Pool**:

```python
# In backend/app/database.py

engine = create_engine(
    str(settings.supabase.url),
    pool_size=25,  # Increased from 20
    max_overflow=15,  # Increased from 10
    pool_pre_ping=True,
    pool_recycle=180,  # Reduced from 300
    pool_timeout=30,
    echo=False,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)
```

### 4. Rate Limiting Optimization

**Implement Tiered Rate Limiting**:

```python
# In backend/app/utils/limiter.py

def get_tiered_rate_limit(request: Request) -> str:
    """Tiered rate limiting based on user type"""
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        # Premium users get higher limits
        if user.get("is_premium", False):
            return "200/minute"
        # Regular users
        return "100/minute"
    # Anonymous users
    return "50/minute"

limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=settings.redis_url,
    strategy="fixed-window"
)
```

## 🔧 Configuration Optimizations

### Nginx Performance Tuning

```nginx
# Add to your nginx.conf

http {
    # Increase worker processes
    worker_processes auto;

    # Optimize worker connections
    events {
        worker_connections 4096;
        multi_accept on;
        use epoll;
    }

    # Buffer and timeout settings
    client_body_buffer_size 128k;
    client_max_body_size 20m;
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 75 75;
    send_timeout 10;

    # Gzip compression
    gzip on;
    gzip_comp_level 6;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Proxy optimizations
    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;
    proxy_temp_file_write_size 256k;
    proxy_max_temp_file_size 0;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
```

### FastAPI Performance Settings

```python
# In backend/app/main.py

app = FastAPI(
    title="AgentsFlowAI API",
    description="AI-powered business automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    # Performance optimizations
    debug=False,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

# Add performance middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add response compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
    compresslevel=6,
)

# Add timeout middleware
app.add_middleware(
    TimeoutMiddleware,
    timeout=30  # 30 second timeout for all requests
)
```

## 📈 Monitoring and Profiling

### Performance Monitoring Setup

```python
# In backend/app/main.py

@app.middleware("http")
async def performance_monitoring(request: Request, call_next):
    """Performance monitoring middleware"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Log performance metrics
    logger.info(
        "Performance",
        extra={
            "path": request.url.path,
            "method": request.method,
            "process_time": f"{process_time:.4f}",
            "status_code": response.status_code,
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": request.client.host if request.client else None
        }
    )

    # Add performance header
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response
```

### Database Query Logging

```python
# In backend/app/database.py

# Enable query logging for slow queries
engine = create_engine(
    str(settings.supabase.url),
    pool_size=25,
    max_overflow=15,
    pool_pre_ping=True,
    pool_recycle=180,
    echo=True,  # Enable for debugging, disable in production
    connect_args={
        "application_name": "agentsflowai",
        "statement_timeout": 5000,  # 5 second query timeout
    }
)

# Add event listener for slow queries
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()
    context._statement = statement

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.5:  # Log queries slower than 500ms
        logger.warning(
            "Slow query",
            extra={
                "query": context._statement,
                "parameters": parameters,
                "duration": f"{total:.4f}",
                "connection": str(conn.engine.url)
            }
        )
```

## 🛡️ Security Performance

### DDoS Protection

```nginx
# Add to nginx.conf

http {
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api_ratelimit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth_ratelimit:10m rate=5r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # In your server block
    server {
        # ...

        location /api/ {
            limit_req zone=api_ratelimit burst=20 nodelay;
            limit_conn conn_limit 10;

            # Additional DDoS protection
            if ($request_method !~ ^(GET|POST|PUT|PATCH|DELETE|OPTIONS)$) {
                return 405;
            }

            if ($http_user_agent ~* (curl|wget|python|java|perl)) {
                return 403;
            }

            # ...
        }

        location /auth/ {
            limit_req zone=auth_ratelimit burst=5 nodelay;
            # ...
        }
    }
}
```

### API Security Headers

```python
# In backend/app/main.py

@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"

    return response
```

## 🔄 Caching Strategies

### Browser Caching

```nginx
# Add to nginx.conf

location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
    access_log off;
}
```

### API Response Caching

```python
# In backend/app/routes/models.py

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Initialize caching
@router.on_event("startup")
async def startup():
    RedisBackend = RedisBackend("redis://localhost:6379")
    FastAPICache.init(RedisBackend, prefix="fastapi-cache")

@router.get("/models", response_model=ModelListResponse)
@cache(expire=300)  # Cache for 5 minutes
async def list_models(
    mm: Optional[ModelManager] = Depends(get_model_manager)
):
    """List all available models with caching"""
    # ... existing implementation
```

## 📊 Performance Testing

### Load Testing Script

```python
# Create backend/tests/performance_test.py

import time
import asyncio
import aiohttp
from datetime import datetime

async def run_performance_test():
    """Run performance test against API endpoints"""
    base_url = "https://api.agentsflow.cloud"
    test_duration = 60  # seconds
    concurrency = 50
    endpoints = [
        "/health",
        "/api/models",
        "/api/models/mistral"
    ]

    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        request_count = 0
        success_count = 0
        error_count = 0
        total_latency = 0

        async def make_request():
            nonlocal request_count, success_count, error_count, total_latency
            while time.time() - start_time < test_duration:
                endpoint = random.choice(endpoints)
                url = f"{base_url}{endpoint}"
                request_start = time.time()

                try:
                    async with session.get(url, timeout=5) as response:
                        latency = time.time() - request_start
                        total_latency += latency
                        request_count += 1

                        if response.status == 200:
                            success_count += 1
                        else:
                            error_count += 1
                            print(f"Error: {response.status} - {url}")

                        # Random delay between requests
                        await asyncio.sleep(random.uniform(0.1, 0.5))

                except Exception as e:
                    error_count += 1
                    print(f"Exception: {str(e)} - {url}")

        # Run concurrent requests
        tasks = [make_request() for _ in range(concurrency)]
        await asyncio.gather(*tasks)

        # Calculate metrics
        elapsed = time.time() - start_time
        rps = request_count / elapsed
        avg_latency = total_latency / request_count if request_count > 0 else 0
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0

        print(f"\nPerformance Test Results ({test_duration}s):")
        print(f"Requests: {request_count}")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Requests per second: {rps:.2f}")
        print(f"Average latency: {avg_latency:.4f}s")
        print(f"Error rate: {error_rate:.2f}%")

if __name__ == "__main__":
    asyncio.run(run_performance_test())
```

## 📈 Performance Metrics Dashboard

### Prometheus Configuration

```yaml
# Create ops/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agentsflowai'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
```

### FastAPI Metrics Endpoint

```python
# In backend/app/routes/metrics.py

from fastapi import APIRouter, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from backend.app.utils.metrics import setup_metrics

router = APIRouter()
setup_metrics()

@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

## 🎯 Optimization Checklist

### Immediate Optimizations (Do Now)
- [ ] Add database indexes for frequently queried columns
- [ ] Implement Redis caching for API responses
- [ ] Tune database connection pool settings
- [ ] Optimize Nginx configuration
- [ ] Enable Gzip compression
- [ ] Implement tiered rate limiting

### Short-Term Optimizations (Next Week)
- [ ] Set up performance monitoring dashboard
- [ ] Implement query logging for slow queries
- [ ] Add browser caching for static assets
- [ ] Optimize Docker image size
- [ ] Implement connection keep-alive
- [ ] Add health check endpoints

### Long-Term Optimizations (Next Month)
- [ ] Implement database read replicas
- [ ] Set up Redis cluster for high availability
- [ ] Add CDN for static assets
- [ ] Implement request batching
- [ ] Add database query optimization
- [ ] Implement auto-scaling

## 📊 Performance Benchmarks

### Target Performance Metrics

| Metric | Current | Target | Status |
|--------|---------|-------|--------|
| API Response Time | 200ms | <100ms | ⚠️ Needs improvement |
| Database Query Time | 50ms | <20ms | ⚠️ Needs optimization |
| Requests per Second | 50 | 200+ | ⚠️ Needs scaling |
| Error Rate | 0.5% | <0.1% | ✅ Good |
| Cache Hit Ratio | 30% | >70% | ⚠️ Needs caching |
| Memory Usage | 512MB | <1GB | ✅ Good |

### Optimization Roadmap

**Week 1: Basic Optimization**
- Implement Redis caching
- Add database indexes
- Tune connection pooling
- Optimize Nginx settings

**Week 2: Advanced Caching**
- Implement multi-level caching
- Add browser caching
- Set up CDN for static assets
- Optimize API responses

**Week 3: Database Optimization**
- Add read replicas
- Implement query optimization
- Set up database monitoring
- Optimize slow queries

**Week 4: Scaling**
- Implement auto-scaling
- Set up load balancing
- Add Redis cluster
- Optimize Docker deployment

## 🆘 Performance Troubleshooting

### Common Performance Issues

**Issue: High API Latency**
```bash
# Check API response times
curl -s -o /dev/null -w "Connect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" https://api.agentsflow.cloud/health

# Check database queries
tail -f /var/log/agentsflowai/api.log | grep "Slow query"

# Check Redis performance
redis-cli --latency-history
```

**Issue: Database Connection Errors**
```bash
# Check connection pool status
python -c "from backend.app.database import engine; print(engine.pool.status())"

# Monitor active connections
psql "your-database-url" -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Check for connection leaks
netstat -anp | grep postgres | wc -l
```

**Issue: High Memory Usage**
```bash
# Check memory usage
docker stats --no-stream

# Analyze Python memory
python -c "import os, psutil; proc = psutil.Process(os.getpid()); print(proc.memory_info().rss / 1024 / 1024, 'MB')"

# Check Redis memory
redis-cli info memory
```

**Issue: Slow Redis Performance**
```bash
# Check Redis latency
redis-cli --latency

# Monitor Redis commands
redis-cli --stat

# Check Redis memory usage
redis-cli info memory | grep used_memory
```

## 🎉 Performance Optimization Summary

This guide provides a comprehensive approach to optimizing AgentsFlowAI performance:

✅ **Immediate Wins**: Database indexes, Redis caching, connection pooling
✅ **Quick Improvements**: Nginx tuning, Gzip compression, rate limiting
✅ **Monitoring**: Performance metrics, slow query logging, health checks
✅ **Security**: DDoS protection, security headers, rate limiting
✅ **Scaling**: Load balancing, auto-scaling, read replicas

**Next Steps:**
1. Implement basic caching and indexing
2. Set up performance monitoring
3. Optimize database queries
4. Tune Nginx and FastAPI settings
5. Monitor and iterate on performance

**Target:** Achieve <100ms average response time with 200+ RPS capacity