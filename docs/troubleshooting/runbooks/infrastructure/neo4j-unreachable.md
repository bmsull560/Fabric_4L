# Runbook: Neo4j Unreachable

## Overview

Neo4j knowledge graph database is unreachable or reporting unhealthy status, impacting graph queries, entity storage, and relationship traversal across all layers.

## Symptoms

- **Alert:** `Neo4jDown`
- **Dashboard:** [Neo4j Performance](../../monitoring/grafana/dashboards/neo4j-performance.json)
- **Log Query:**
  ```
  {component="neo4j"} |= "Connection refused" 
  or
  {layer="layer3"} |= "Neo4jError\|ServiceUnavailable"
  ```
- **User Impact:** Graph Explorer fails to load, entity searches return errors, relationship queries timeout
- **Metrics:**
  - `value_fabric_health_status{component="neo4j"} == 0`
  - `neo4j_transaction_active_count` dropping to 0
  - Layer 3 API error rate spike

## Diagnosis

### 1. Check Neo4j Pod Status

```bash
# Check pod status and events
kubectl get pods -n value-fabric -l app=neo4j
kubectl describe pod -n value-fabric -l app=neo4j

# Check for recent restarts or OOMKilled
kubectl get pods -n value-fabric -l app=neo4j -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}'
```

### 2. Verify Neo4j Logs

```bash
# Check for OOM, disk, or license errors
kubectl logs -n value-fabric -l app=neo4j --tail=100

# Check Neo4j specific errors
kubectl logs -n value-fabric -l app=neo4j | grep -E "ERROR|FATAL|OutOfMemory|disk full"

# Check kernel logs if pod is crash looping
kubectl logs -n value-fabric -l app=neo4j --previous 2>/dev/null | tail -50
```

### 3. Check Resource Constraints

```bash
# Check memory usage
kubectl top pod -n value-fabric -l app=neo4j

# Check PVC disk usage
kubectl exec -n value-fabric -it deployment/neo4j -- \
  df -h /data

# Check Neo4j memory config
kubectl exec -n value-fabric -it deployment/neo4j -- \
  cat /var/lib/neo4j/conf/neo4j.conf | grep memory
```

### 4. Verify Network Connectivity

```bash
# Test from Layer 3 pod
kubectl exec -n value-fabric -it deployment/layer3-knowledge -- \
  nc -zv neo4j 7687

# Test Bolt protocol
kubectl exec -n value-fabric -it deployment/layer3-knowledge -- \
  curl -s neo4j:7474/db/manage/server/jmx/domain/org.neo4j/instance%3Dkernel%230%2Cname%3DDiagnostics

# Check service endpoints
kubectl get endpoints -n value-fabric neo4j
```

## Remediation

### Immediate Actions (P0)

1. **Restart Neo4j Pod (if stuck or OOMKilled)**
   ```bash
   # Graceful restart
   kubectl rollout restart deployment/neo4j -n value-fabric
   
   # Wait for readiness
   kubectl wait --for=condition=ready pod -l app=neo4j -n value-fabric --timeout=120s
   ```

2. **Check and Free Disk Space (if disk full)**
   ```bash
   # Check disk usage
   kubectl exec -n value-fabric -it deployment/neo4j -- du -sh /data/* | sort -hr | head -10
   
   # If logs consuming space, truncate
   kubectl exec -n value-fabric -it deployment/neo4j -- \
     find /var/log/neo4j -name "*.log.*" -mtime +7 -delete
   
   # Check transaction logs
   kubectl exec -n value-fabric -it deployment/neo4j -- \
     ls -la /data/databases/neo4j/transactions/
   ```

3. **Increase Memory Limits (if OOM)**
   ```bash
   # Edit deployment to increase memory
   kubectl set resources deployment/neo4j -n value-fabric \
     --limits=memory=8Gi --requests=memory=4Gi
   
   # Restart to apply
   kubectl rollout restart deployment/neo4j -n value-fabric
   ```

### Short-Term Mitigation (P1)

4. **Verify/Fix License (if license error)**
   ```bash
   # Check license status
   kubectl exec -n value-fabric -it deployment/neo4j -- \
     cypher-shell -u neo4j -p $NEO4J_PASSWORD "CALL dbms.components() YIELD name, edition"
   
   # Check for license file
   kubectl get secret -n value-fabric neo4j-license -o jsonpath='{.data.license}' | base64 -d
   ```

5. **Enable Read Replicas (if available)**
   ```bash
   # Check if read replicas exist
   kubectl get pods -n value-fabric -l app=neo4j-read-replica
   
   # Route read traffic to replicas temporarily
   kubectl set env deployment/layer3-knowledge \
     NEO4J_READ_REPLICA_ENABLED=true \
     NEO4J_READ_REPLICA_URI="bolt://neo4j-read-replica:7687"
   ```

### Data Recovery (if corruption suspected)

6. **Restore from Backup**
   ```bash
   # List available backups
   kubectl exec -n value-fabric -it deployment/neo4j-backup -- \
     ls -la /backups/
   
   # Restore latest backup (destructive - confirm first!)
   kubectl exec -n value-fabric -it deployment/neo4j -- \
     neo4j-admin database restore --from-path=/backups/neo4j-$(date +%Y%m%d).backup --database=neo4j --force
   
   # Restart after restore
   kubectl rollout restart deployment/neo4j -n value-fabric
   ```

## Verification

### Confirm Service Recovery

```bash
# Check health endpoint
kubectl exec -n value-fabric -it deployment/neo4j -- \
  curl -s http://localhost:7474/db/manage/server/availability | jq

# Expected: {"status": "available"}

# Test from Layer 3
kubectl exec -n value-fabric -it deployment/layer3-knowledge -- \
  python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password'))
with driver.session() as s:
    print(s.run('RETURN 1 as n').single()['n'])
"

# Monitor graph queries for 2 minutes
kubectl logs -n value-fabric -l app=layer3-knowledge --tail=50 | grep -c "200 OK"
```

## Escalation

- **If restart does not resolve within 5 minutes:** Page `vf-db-oncall` via PagerDuty
- **If data corruption suspected:** Escalate to Database Architecture team immediately
- **If cluster failover needed:** Contact Platform team for cluster promotion
- **PagerDuty rotation:** `vf-db-oncall` schedule
- **Slack channel:** `#vf-db-oncall`

## Post-Incident Actions

1. Document root cause (OOM, disk full, license, corruption, network)
2. Update resource limits if OOM was cause
3. Review backup restoration process if used
4. Consider enabling Neo4j causal cluster for HA

## Related Runbooks

- [High Memory Usage](./high-memory-usage.md) - If OOM-related
- [Disk Space Critical](./disk-space-critical.md) - If disk-related
- [Service Down](./service-down.md) - General service recovery

## References

- Neo4j Operations Manual: https://neo4j.com/docs/operations-manual/current/
- Neo4j Kubernetes Helm Chart: `k8s/base/neo4j.yaml`
- Layer 3 Neo4j Client: `value-fabric/layer3-knowledge/src/db/neo4j_client.py`

---

> **Policy reference:** [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md)
