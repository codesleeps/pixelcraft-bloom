# Capacity Planning and Scaling Guide

This document outlines the capacity planning strategy and scaling thresholds for PixelCraft Bloom.

## Baseline Metrics

Based on initial load testing (simulated):

*   **Average Response Time (Chat)**: < 500ms (excluding LLM generation time)
*   **Average Response Time (Analytics)**: < 200ms (cached)
*   **Throughput**: Capable of handling ~100 requests/second on a standard 2 vCPU / 4GB RAM instance.

## Resource Limits & Bottlenecks

1.  **Database Connections (Supabase)**
    *   **Limit**: Depends on plan (e.g., 60 connections for Pro).
    *   **Bottleneck**: High concurrency analytics queries or chat logs.
    *   **Mitigation**: Use connection pooling (Supavisor) and Redis caching for read-heavy data.

2.  **Redis Memory**
    *   **Usage**: Caching analytics, rate limiting counters, Pub/Sub.
    *   **Threshold**: Alert at 80% memory usage.
    *   **Mitigation**: Set appropriate TTLs (already implemented) and eviction policies (`allkeys-lru`).

3.  **Application Server (FastAPI/Uvicorn)**
    *   **CPU**: Primary constraint for JSON serialization and async loop management.
    *   **Memory**: Generally stable, but monitor for leaks.
    *   **Scaling**: Horizontal scaling (add more replicas) behind a load balancer (Nginx/AWS ALB).

## Scaling Thresholds

| Metric | Threshold | Action |
| :--- | :--- | :--- |
| **CPU Usage** | > 70% for 5 mins | Scale out (add +1 replica) |
| **Memory Usage** | > 80% for 5 mins | Scale out or Resize instance |
| **Response Time (p95)** | > 2000ms | Investigate DB/LLM latency, consider caching |
| **Error Rate (5xx)** | > 1% | Trigger Critical Alert |

## Load Testing Strategy

Run load tests before major releases or marketing events.

**Command:**
```bash
./ops/run-load-tests.sh
```

**Scenarios:**
1.  **Smoke Test**: 10 users, verify system health.
2.  **Load Test**: 100 users, verify performance under expected load.
3.  **Stress Test**: Ramp up until failure to find breaking point.
