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
- **Chat Endpoint**: Successfully handled traffic up to rate limit (100 req/min).
  - *Observation*: Rate limiting works as expected (429 responses).
  - *Stability*: Backend remained stable with no 500 errors after fixes.
- **Analytics Endpoints**: Protected by authentication (401 responses in test).
  - *Recommendation*: Use authenticated users for future tests to stress DB.
- **Performance**:
  - Average Response Time: ~20ms (cached/fallback), ~200ms (uncached).
  - 95th Percentile: ~50ms.

## 5. Capacity Recommendations
1. **Rate Limiting**: Keep current limits (100/min for chat) to protect resources.
2. **Caching**: Ensure Redis is persistent and monitored.
3. **Database**: Monitor connection usage during peak hours.
4. **AI Inference**: Move to dedicated inference server if local CPU/GPU is bottleneck.
