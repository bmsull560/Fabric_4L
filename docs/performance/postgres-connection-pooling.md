# PostgreSQL Connection Pool Tuning Guide

Production guidance for sizing database connection pools across all Value Fabric layers.

## Quick Reference

| Layer | Pool Size | Max Overflow | Timeout | Rationale |
|-------|-----------|--------------|---------|-----------|
| **L1 - Ingestion** | 10 | 5 | 30s | Burst ingestion, short queries |
| **L2 - Extraction** | 15 | 10 | 60s | LLM batch processing, longer queries |
| **L3 - Knowledge** | 20 | 10 | 30s | Graph-heavy queries, high concurrency |
| **L4 - Agents** | 25 | 15 | 30s | Workflow checkpointing, sustained load |
| **L5 - Ground Truth** | 10 | 5 | 30s | Evaluation persistence, lower volume |
| **L6 - Benchmarks** | 5 | 3 | 15s | Benchmark storage, minimal needs |

## Connection Pool Formula

Calculate your pool size using:

```
connections = ((core_count * 2) + effective_spindle_count) / service_count
```

For Kubernetes deployments:

```
pool_size = (CPU_cores * 2) / replica_count
max_overflow = pool_size / 2
```

## Configuration Examples

### SQLAlchemy + asyncpg (Layer 3)

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,      # Recycle connections hourly
    pool_pre_ping=True,     # Verify connections before use
    echo=False,
)
```

### Psycopg3 (Layer 1, 2)

```python
from psycopg_pool import AsyncConnectionPool

pool = AsyncConnectionPool(
    conninfo=DATABASE_URL,
    min_size=10,
    max_size=15,
    timeout=30,
    max_idle=300,           # Close idle connections after 5 min
    max_lifetime=3600,      # Recycle after 1 hour
)
```

## Kubernetes Configuration

### Connection Pool Annotations

Add to layer Deployment manifests:

```yaml
metadata:
  annotations:
    # Pool sizing hints for monitoring
    postgres.pool.size: "20"
    postgres.pool.max-overflow: "10"
    postgres.pool.timeout: "30s"
    
    # Connection lifecycle
    postgres.pool.recycle: "3600"
    postgres.pool.pre-ping: "true"
spec:
  template:
    spec:
      containers:
        - name: api
          env:
            - name: DATABASE_POOL_SIZE
              value: "20"
            - name: DATABASE_MAX_OVERFLOW
              value: "10"
            - name: DATABASE_POOL_TIMEOUT
              value: "30"
            - name: DATABASE_POOL_RECYCLE
              value: "3600"
```

## Monitoring

### Key Metrics

1. **Pool Utilization**
   ```promql
   sqlalchemy_pool_checkedin / sqlalchemy_pool_size
   ```
   Alert if > 80% for > 5 minutes

2. **Overflow Usage**
   ```promql
   sqlalchemy_pool_overflow > 0
   ```
   Alert if consistently > 0

3. **Connection Wait Time**
   ```promql
   rate(sqlalchemy_pool_wait_time_seconds_total[5m])
   ```
   Alert if p95 > 1s

### Prometheus Recording Rules

```yaml
groups:
  - name: postgres_pool_alerts
    rules:
      - alert: PostgresPoolExhaustion
        expr: |
          (
            sqlalchemy_pool_checkedin + sqlalchemy_pool_overflow
          ) / sqlalchemy_pool_size > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool near exhaustion"
          description: "{{ $labels.service }} pool utilization > 90%"
          
      - alert: PostgresPoolWaitTimeHigh
        expr: |
          histogram_quantile(0.95,
            rate(sqlalchemy_pool_wait_time_seconds_bucket[5m])
          ) > 1
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "High database connection wait times"
```

## Troubleshooting

### Symptom: "QueuePool limit of size X overflow Y reached"

**Cause:** Connection pool exhausted  
**Solutions:**
1. Increase `pool_size` if connections are legitimately needed
2. Decrease `pool_size` and enable connection pooling in pgBouncer
3. Check for connection leaks (unclosed transactions)
4. Reduce query duration

### Symptom: Idle connections not closing

**Cause:** No `pool_recycle` or `max_lifetime` set  
**Solutions:**
```python
# Add to engine configuration
pool_recycle=3600,      # Recycle after 1 hour
pool_pre_ping=True,     # Detect stale connections
```

### Symptom: Slow startup on pod creation

**Cause:** Pre-ping checking all connections  
**Solutions:**
```python
# Disable pre-ping for faster startup
pool_pre_ping=False

# Or reduce pool size for init
pool_size=5,
max_overflow=10,
```

## Optimization Patterns

### Pattern 1: Read Replicas

For L3 (read-heavy workloads):

```python
# Primary for writes
write_engine = create_async_engine(
    PRIMARY_URL,
    pool_size=5,  # Smaller pool for writes
)

# Replicas for reads
read_engine = create_async_engine(
    REPLICA_URL,
    pool_size=30,  # Larger pool for reads
)
```

### Pattern 2: Separate Pools by Operation Type

```python
# Fast operations pool
fast_engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    pool_timeout=5,
)

# Slow operations pool (reports, analytics)
slow_engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    pool_timeout=120,
)
```

## Validation Checklist

- [ ] Pool size based on `(cores * 2) / replicas` formula
- [ ] Max overflow at 50% of pool size
- [ ] Pool timeout < query timeout
- [ ] Pool recycle enabled (3600s)
- [ ] Pre-ping enabled for production
- [ ] Metrics exposed for monitoring
- [ ] Alerts configured for exhaustion
- [ ] Load tested with k6 scenarios
