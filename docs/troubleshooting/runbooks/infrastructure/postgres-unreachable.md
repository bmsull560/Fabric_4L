# Runbook: PostgreSQL Unreachable

## Overview

PostgreSQL database is unreachable or reporting unhealthy status, impacting SQL-dependent services (Layer 1, Layer 4, Layer 5) that cannot persist state.

## Symptoms

- **Alert:** `PostgresDown`
- **Dashboard:** [Layer 4 Agents](../../monitoring/grafana/dashboards/layer4-agents.json) (contains DB connection metrics)
- **Log Query:**
  ```
  {component="postgres"} |= "connection failed\|FATAL\|could not connect"
  or
  {layer="layer4"} |= "sqlalchemy.exc.OperationalError\|psycopg2.OperationalError"
  ```
- **User Impact:** Workflows fail, agent state cannot be saved, user sessions may be lost
- **Metrics:**
  - `layer4_health_status{component="postgres"} == 0`
  - `layer4_db_connection_pool_available` dropping to 0
  - SQL-dependent API endpoints returning 500/503 errors

## Diagnosis

### 1. Check PostgreSQL Pod Status

```bash
# Check pod status and events
kubectl get pods -n value-fabric -l app=postgres
kubectl describe pod -n value-fabric -l app=postgres

# Check for recent restarts
kubectl get pods -n value-fabric -l app=postgres \
  -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}'
```

### 2. Verify PostgreSQL Logs

```bash
# Check for connection limit, lock, or crash errors
kubectl logs -n value-fabric -l app=postgres --tail=100

# Look for specific error patterns
kubectl logs -n value-fabric -l app=postgres | grep -E \
  "FATAL|ERROR|connection limit|lock|deadlock|out of memory"

# Check previous container logs if crash looping
kubectl logs -n value-fabric -l app=postgres --previous 2>/dev/null | tail -50
```

### 3. Check Connection Status

```bash
# Check active connections
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -U postgres -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check max_connections setting
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -U postgres -c "SHOW max_connections;"

# Check for idle connections
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -U postgres -c "SELECT pid, state, usename, application_name, state_change FROM pg_stat_activity WHERE state = 'idle' ORDER BY state_change;"
```

### 4. Verify PVC and Disk Health

```bash
# Check PVC status
kubectl get pvc -n value-fabric -l app=postgres

# Check disk space from inside pod
kubectl exec -n value-fabric -it deployment/postgres -- \
  df -h /var/lib/postgresql/data

# Check PostgreSQL data directory size
kubectl exec -n value-fabric -it deployment/postgres -- \
  du -sh /var/lib/postgresql/data

# Check WAL directory if separate
kubectl exec -n value-fabric -it deployment/postgres -- \
  du -sh /var/lib/postgresql/data/pg_wal 2>/dev/null || echo "WAL in data dir"
```

## Remediation

### Immediate Actions (P0)

1. **Restart PostgreSQL Pod (if unresponsive)**
   ```bash
   # Graceful restart
   kubectl rollout restart deployment/postgres -n value-fabric

   # Wait for readiness
   kubectl wait --for=condition=ready pod -l app=postgres -n value-fabric --timeout=120s
   ```

2. **Increase max_connections (if limit reached)**
   ```bash
   # Check current connections
   kubectl exec -n value-fabric -it deployment/postgres -- \
     psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

   # Temporarily increase max_connections
   kubectl exec -n value-fabric -it deployment/postgres -- \
     psql -U postgres -c "ALTER SYSTEM SET max_connections = 200;"

   # Reload configuration
   kubectl exec -n value-fabric -it deployment/postgres -- \
     psql -U postgres -c "SELECT pg_reload_conf();"

   # Permanent fix via ConfigMap
   kubectl edit configmap postgres-config -n value-fabric
   # Add: max_connections = 200
   ```

3. **Terminate Idle Connections (if connection limit reached)**
   ```bash
   # Identify and terminate idle connections (be careful!)
   kubectl exec -n value-fabric -it deployment/postgres -- \
     psql -U postgres -c "
     SELECT pg_terminate_backend(pid)
     FROM pg_stat_activity
     WHERE state = 'idle'
     AND state_change < NOW() - INTERVAL '10 minutes';
     "
   ```

### Short-Term Mitigation (P1)

4. **Failover to Standby (if HA configured)**
   ```bash
   # Check if standby exists
   kubectl get pods -n value-fabric -l app=postgres-replica

   # Promote standby to primary (if using Patroni or repmgr)
   kubectl exec -n value-fabric -it deployment/postgres-replica -- \
     patronictl failover postgres

   # Update service selector to point to new primary
   kubectl patch service postgres -n value-fabric -p \
     '{"spec":{"selector":{"role":"primary"}}}'
   ```

5. **Enable Connection Pooling (PgBouncer)**
   ```bash
   # Check if PgBouncer exists
   kubectl get pods -n value-fabric -l app=pgbouncer

   # Enable PgBouncer in Layer 4 config
   kubectl set env deployment/layer4-agents \
     DB_USE_POOLER=true \
     DB_POOLER_HOST=pgbouncer \
     DB_POOLER_PORT=5432

   # Restart Layer 4 to apply
   kubectl rollout restart deployment/layer4-agents -n value-fabric
   ```

### Data Recovery (if corruption suspected)

6. **Restore from Backup**
   ```bash
   # List available backups
   kubectl exec -n value-fabric -it deployment/postgres-backup -- \
     ls -la /backups/

   # Restore from latest backup (destructive - confirm first!)
   kubectl exec -n value-fabric -it deployment/postgres -- \
     pg_restore --clean --if-exists /backups/postgres-$(date +%Y%m%d).dump

   # Or use WAL-E/WAL-G for point-in-time recovery
   kubectl exec -n value-fabric -it deployment/postgres -- \
     envdir /etc/wal-e.d/env wal-e backup-fetch /var/lib/postgresql/data LATEST
   ```

## Verification

### Confirm Service Recovery

```bash
# Test database connectivity
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -U postgres -c "SELECT 1;"

# Test from Layer 4
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "
import asyncio
from layer4_agents.db import get_db
async def test():
    db = await get_db()
    result = await db.fetchval('SELECT 1')
    print(f'DB test: {result}')
asyncio.run(test())
"

# Check connection pool status
kubectl logs -n value-fabric -l app=layer4-agents --tail=20 | grep -i "database\|connection"

# Monitor API health
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  curl -s http://localhost:8000/health | jq '.dependencies.postgres'
```

## Escalation

- **If failover or restart fails:** Page `vf-db-oncall` via PagerDuty immediately
- **If data corruption suspected:** Escalate to Database Architecture team
- **If connection limit reached repeatedly:** Contact Platform team for pool configuration review
- **PagerDuty rotation:** `vf-db-oncall` schedule
- **Slack channel:** `#vf-db-oncall`

## Post-Incident Actions

1. Document root cause (connection limit, disk full, crash, corruption)
2. Update connection pool configuration if limit was issue
3. Review backup restoration process if used
4. Consider enabling PgBouncer or connection pooling
5. Review long-running queries that may be holding connections

## Related Runbooks

- [High Error Rate](./high-error-rate.md) - If cascading errors from DB failure
- [Disk Space Critical](./disk-space-critical.md) - If disk-related
- [Service Down](./service-down.md) - General service recovery

## References

- PostgreSQL Documentation: https://www.postgresql.org/docs/current/
- Layer 4 Database Client: `services/layer4-agents/src/db/`
- Kubernetes Postgres Config: `k8s/base/postgres.yaml`

---

> **Policy reference:** [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md)
