# Runbook: SlowQueries

## Overview

Query latency degradation detected with p95 response times exceeding 2 seconds. This indicates database performance issues, missing indexes, or resource contention that will cascade to user-facing timeouts.

## Trigger

- **Alert:** `SlowQueries`
- **Condition:** `histogram_quantile(0.95, sum(rate(layerN_http_request_duration_seconds_bucket[10m])) by (le)) > 2` for 10 minutes
- **Dashboard:** [API Performance](../../monitoring/grafana/dashboards/api-performance.json) → Latency panel

## Impact

- **Severity:** P2 - Degraded performance
- **User Impact:** Slow page loads, timeouts on complex queries, frustrated users
- **Business Impact:** Reduced conversion, increased support tickets
- **Technical Impact:** Connection pool exhaustion, cascading timeouts, retry storms

## Diagnosis

### 1. Identify Affected Layer and Endpoint

```bash
# Check latency by layer
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  curl -s http://localhost:8000/metrics | grep http_request_duration_seconds

# Find slowest endpoints
curl -s http://prometheus:9090/api/v1/query?query='topk(10, sum by (handler) (rate(http_request_duration_seconds_sum[5m])) / sum by (handler) (rate(http_request_duration_seconds_count[5m])))'
```

### 2. Database Query Analysis

**Postgres Slow Query Log:**
```bash
# Check for queries >1s
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements WHERE mean_exec_time > 1000 ORDER BY mean_exec_time DESC LIMIT 10;"

# Check active queries
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "SELECT pid, query_start, state, query FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - interval '5 seconds';"
```

**Neo4j Query Log:**
```bash
# Check slow queries
kubectl exec -n value-fabric -it deployment/neo4j -- \
  cypher-shell "CALL db.stats.retrieve('QUERIES') YIELD section, data RETURN data.query, data.elapsedTimeMillis ORDER BY data.elapsedTimeMillis DESC LIMIT 10"
```

### 3. Resource Contention Check

```bash
# Connection pool status
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "from src.database import engine; print(f'Pool: {engine.pool.size()}/{engine.pool.checkedout()}')"

# CPU/Memory on database pods
kubectl top pods -n value-fabric -l app=postgres
kubectl top pods -n value-fabric -l app=neo4j

# Lock contention
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "SELECT blocked_locks.pid AS blocked_pid, blocked_activity.usename AS blocked_user, blocking_locks.pid AS blocking_pid FROM pg_catalog.pg_locks blocked_locks JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype WHERE NOT blocked_locks.granted;"
```

## Immediate Containment

### 1. Kill Blocking Queries

```bash
# Identify and terminate long-running queries (use with caution)
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - interval '30 seconds' AND query NOT LIKE '%pg_stat%';"

# Neo4j query termination
kubectl exec -n value-fabric -it deployment/neo4j -- \
  cypher-shell "CALL dbms.listQueries() YIELD queryId, query, elapsedTimeMillis WHERE elapsedTimeMillis > 30000 CALL dbms.killQuery(queryId) YIELD username RETURN queryId, username"
```

### 2. Scale Resources

```bash
# Scale up database replicas
kubectl scale deployment/postgres-replica -n value-fabric --replicas=3

# Scale up affected layer
kubectl scale deployment/layer4-agents -n value-fabric --replicas=5
```

### 3. Circuit Breaker Activation

```bash
# Enable circuit breaker for slow endpoints (if feature flags configured)
kubectl patch configmap feature-flags -n value-fabric --type merge -p '{"data":{"CIRCUIT_BREAKER_ENABLED":"true"}}'
```

## Remediation

### Quick Fix: Query Optimization

```bash
# Add missing index (example - adjust column names)
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflows_status ON workflows(status, created_at);"

# Vacuum and analyze
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "VACUUM ANALYZE workflows;"
```

### Root Cause Analysis

```sql
-- Find missing indexes
SELECT 
    schemaname,
    tablename,
    attname as column,
    n_tup_read as idx_reads,
    n_tup_fetch as seq_reads,
    CASE WHEN n_tup_read > 0 THEN n_tup_fetch::float/n_tup_read ELSE 0 END as ratio
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY n_tup_fetch DESC;

-- Check table bloat
SELECT schemaname, tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples
FROM pg_stat_user_tables 
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

## Rollback

If index changes cause issues:

```sql
-- Drop index if problematic
DROP INDEX CONCURRENTLY IF EXISTS idx_workflows_status;

-- Restore previous query plan
-- (May require ANALYZE on affected tables)
ANALYZE workflows;
```

## Validation

```bash
# Verify latency improved
curl -s http://prometheus:9090/api/v1/query?query='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))'

# Check connection pool cleared
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "from src.database import engine; print(f'Active: {engine.pool.checkedout()}')"

# Run smoke test
curl -sf https://api.valuefabric.io/v1/health && echo "Health: OK"
```

## Escalation

| Condition | Action |
|-----------|--------|
| p95 > 5s | Page platform on-call `#vf-platform-oncall` |
| Database CPU > 90% | Escalate to DBA `#vf-dba-oncall` |
| Lock contention detected | Immediate DBA escalation |
| >30 min to resolve | Page engineering lead |

## Prevention

- **Query timeout:** Set `statement_timeout = 30s` in Postgres
- **Index monitoring:** Weekly `pg_stat_statements` review
- **Query plan caching:** Use prepared statements for hot paths
- **Circuit breakers:** Fail fast on >2s queries
- **Performance testing:** Include query latency in CI benchmarks
- **Alert tuning:** Warn at p95 > 1s, critical at >5s

---

**Related Runbooks:**
- [High Memory Usage](high-memory-usage.md) - Resource exhaustion
- [Postgres Unreachable](postgres-unreachable.md) - Database connectivity
- [Neo4j Unreachable](neo4j-unreachable.md) - Graph database issues
