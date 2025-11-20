# Capacity Planning & Load Testing Strategy

## 1. Baseline Metrics (Estimated)
| Resource | Baseline (Idle) | Per Active User | Max Capacity (Current) |
|----------|----------------|-----------------|------------------------|
| CPU      | 5%             | 2%              | 50 Concurrent Users    |
| Memory   | 512MB          | 10MB            | 100 Concurrent Users   |
| DB Conns | 5              | 1               | 50 Connections         |
| Network  | 10KB/s         | 50KB/s          | 100Mbps                |

## 2. Resource Limits & Bottlenecks
- **Database**: Supabase free tier has connection limits (approx 60).
  - *Mitigation*: Use connection pooling (PgBouncer) and cache frequent queries.
- **Redis**: Used for caching and rate limiting. Memory is the constraint.
  - *Mitigation*: Set TTL on all keys, monitor eviction rate.
- **AI Models**: External API rate limits (Ollama/HuggingFace) or local GPU VRAM.
  - *Mitigation*: Queue requests, implement fallback models, cache responses.

## 3. Scaling Thresholds
| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|--------------------|--------|
| CPU Usage | 70% | 90% | Scale out API replicas |
| Memory Usage | 75% | 90% | Scale out API replicas |
| DB CPU | 60% | 85% | Optimize queries, upgrade DB plan |
| Response Time (p95) | 500ms | 2000ms | Investigate bottlenecks, enable aggressive caching |

## 4. Load Testing Strategy
### Tools
- **Locust**: For generating load and simulating user behavior.
- **Script**: `backend/tests/load/locustfile.py`

### Scenarios
1. **Chat Traffic**: Simulate users sending messages and receiving streaming responses.
   - *Goal*: Test throughput of `ChatAgent` and `ModelManager`.
2. **Analytics Dashboard**: Simulate admins viewing high-level metrics.
   - *Goal*: Test DB query performance and caching effectiveness.

### Execution
Run the load test script:
```bash
./ops/run-load-tests.sh
```

### Recent Test Results (Nov 2025)
- **Chat Endpoint**:
  - **Result**: Rate limit exceeded (429) as expected at high load.
  - **Throughput**: Sustained ~50 req/sec before rate limiting kicked in.
  - **Stability**: No 500 errors observed on chat endpoints.
- **Analytics Endpoints**:
  - **Result**: 500 Internal Server Errors observed during load test.
  - **Cause**: Missing local database connection (Supabase) in test environment.
  - **Action Required**: Ensure local Supabase instance is running (`npx supabase start`) before running analytics load tests.
- **Authentication**:
  - Successfully implemented mock authentication for load testing using test tokens.


## 5. Capacity Recommendations
1. **Rate Limiting**: Keep current limits (100/min for chat) to protect resources.
2. **Caching**: Ensure Redis is persistent and monitored.
3. **Database**: Monitor connection usage during peak hours.
4. **AI Inference**: Move to dedicated inference server if local CPU/GPU is bottleneck.
