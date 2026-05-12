# Runbook: ServiceDown

## Overview

Complete service unavailability detected via health check or synthetic probe failure. This is the most critical operational incident requiring immediate response.

## Trigger

- **Alert:** `ServiceDown`
- **Dashboard:** [Value Fabric Health](../../monitoring/grafana/dashboards/value-fabric-health.json)
- **Detection:**
  - Health endpoint returns non-200 for >2 minutes
  - Load balancer marks all instances unhealthy
  - Synthetic probe failure rate >50%
  - Zero successful requests in 2-minute window

## Impact

- **Severity:** P0 - Complete platform outage
- **User Impact:** All users unable to access Value Fabric
- **Business Impact:** Revenue loss, SLA breach, customer escalation
- **Data Impact:** In-flight operations may fail, queued jobs may stall

## Diagnosis

### 1. Verify Scope of Outage

```bash
# Check each layer health endpoint
for layer in layer1-ingestion layer2-extraction layer3-knowledge layer4-agents; do
  echo "=== $layer ==="
  kubectl exec -n value-fabric -it deployment/$layer -- \
    curl -s http://localhost:8000/health | jq '.status, .dependencies'
done
```

### 2. Check Infrastructure Layer

```bash
# Kubernetes pod status
kubectl get pods -n value-fabric -o wide

# Check for CrashLoopBackOff or ImagePullBackOff
kubectl get pods -n value-fabric | grep -E "CrashLoopBackOff|ImagePullBackOff|Error"

# Node status
kubectl get nodes -o wide

# Recent events
kubectl get events -n value-fabric --sort-by='.lastTimestamp' | tail -20
```

### 3. Check Dependencies

```bash
# Database connectivity
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "from src.database import engine; print('DB: OK')"

# Redis connectivity
kubectl exec -n value-fabric -it deployment/layer1-ingestion -- \
  python -c "import redis; r = redis.from_url('$REDIS_URL'); print('Redis: OK')"

# Neo4j connectivity
kubectl exec -n value-fabric -it deployment/layer3-knowledge -- \
  curl -s $NEO4J_URI | jq '.neo4j_version'
```

### 4. Review Recent Changes

```bash
# Check recent deployments
kubectl rollout history deployment/layer4-agents -n value-fabric
kubectl rollout history deployment/layer3-knowledge -n value-fabric

# Check ConfigMap changes
kubectl get configmaps -n value-fabric -o yaml | grep -A5 "resourceVersion"

# Check secret rotations
kubectl get events -n value-fabric | grep -i secret
```

## Immediate Containment

### 1. Page On-Call Engineer

```bash
# Trigger PagerDuty alert
pd incident:create --title="Value Fabric Service Down" \
  --service="value-fabric-production" \
  --urgency="high" \
  --priority="P0"
```

### 2. Status Page Update

```bash
# Update status page
statuspage incident:create --page="value-fabric" \
  --name="Platform Unavailable" \
  --status="investigating" \
  --impact="major"
```

### 3. Communication

- Post in `#incidents` Slack channel
- Notify customer success team
- Prepare executive briefing if >15 minutes

## Remediation

### Scenario 1: Pod Crash/Restart

```bash
# Check logs for panic
kubectl logs -n value-fabric -l app=layer4-agents --previous | tail -100

# If specific pod unhealthy, delete it (replacement will spawn)
kubectl delete pod -n value-fabric <pod-name>

# If deployment-wide issue, rollback to previous revision
kubectl rollout undo deployment/layer4-agents -n value-fabric
kubectl rollout status deployment/layer4-agents -n value-fabric --timeout=120s
```

### Scenario 2: Database Connection Pool Exhaustion

```bash
# Check active connections
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "
from src.database import engine
import asyncio
async def check_pool():
    print(f'Pool size: {engine.pool.size()}')
    print(f'Checked in: {engine.pool.checkedin()}')
    print(f'Checked out: {engine.pool.checkedout()}')
asyncio.run(check_pool())
"

# Restart affected layer to reset connections
kubectl rollout restart deployment/layer4-agents -n value-fabric
```

### Scenario 3: Memory/Resource Exhaustion

```bash
# Check resource usage
kubectl top pods -n value-fabric

# Check for OOMKilled
kubectl get pods -n value-fabric -o json | jq '.items[].status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled")'

# Scale up if resource constrained
kubectl scale deployment/layer4-agents -n value-fabric --replicas=5
```

### Scenario 4: Dependency Failure (Neo4j/Postgres/Redis)

```bash
# If Neo4j down
kubectl get pods -n value-fabric -l app=neo4j
kubectl describe pod neo4j-0 -n value-fabric

# If Postgres down
kubectl get pods -n value-fabric -l app=postgres
kubectl logs -n value-fabric -l app=postgres --tail=50

# Check if dependency is the root cause or symptom
kubectl get events -n value-fabric --field-selector reason=FailedMount
```

## Rollback

If remediation fails:

```bash
# Emergency rollback to previous stable version
kubectl rollout undo deployment/layer4-agents -n value-fabric --to-revision=<last-known-good>
kubectl rollout undo deployment/layer3-knowledge -n value-fabric --to-revision=<last-known-good>

# Verify rollback
kubectl get pods -n value-fabric
kubectl rollout status deployment/layer4-agents -n value-fabric
```

## Validation

### 1. Health Check Verification

```bash
# All layers must return healthy
for layer in layer1-ingestion layer2-extraction layer3-knowledge layer4-agents; do
  echo "Checking $layer..."
  kubectl exec -n value-fabric -it deployment/$layer -- \
    curl -sf http://localhost:8000/health && echo " ✅" || echo " ❌"
done
```

### 2. Synthetic Probe

```bash
# Run smoke test
curl -sf https://api.valuefabric.io/v1/health && echo "API: ✅"
curl -sf https://app.valuefabric.io/ && echo "Frontend: ✅"
```

### 3. Functional Test

```bash
# Test critical path: Query knowledge graph
curl -X POST https://api.valuefabric.io/v1/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}' | jq '.results | length'
```

## Escalation

| Time Elapsed | Action |
|--------------|--------|
| 0-5 min | On-call engineer engaged, diagnosis started |
| 5-15 min | If no clear cause, escalate to platform team |
| 15-30 min | Executive notification, war room activated |
| 30+ min | Consider failover to DR region if configured |

**Escalation Endpoints (production):**
- **Primary paging:** PagerDuty service `pagerduty-critical` (platform-engineering path)
- **Primary responder channel:** Slack `#vf-alerts-critical`
- **Secondary responder schedule:** PagerDuty schedule `sre-secondary`
- **Incident command channel:** Slack `#incident-response`
- **Executive escalation (SEV-0 / >15 min):** PagerDuty schedule `engineering-lead-secondary` and alias `@vf-eng-leadership`

## Prevention

- Enable pod disruption budgets for minimum availability
- Configure horizontal pod autoscaling
- Implement circuit breakers for dependency calls
- Regular chaos engineering exercises
- Blue/green deployments with automated rollback

---

**Related Runbooks:**
- [Neo4j Unreachable](neo4j-unreachable.md)
- [Postgres Unreachable](postgres-unreachable.md)
- [Redis Unreachable](redis-unreachable.md)
- [High Error Rate](high-error-rate.md)


## Tabletop Drill Evidence

- Latest ServiceDown tabletop drill (SEV-0 outage simulation): `docs/operations/evidence/tabletop-drill-2026-05-12-servicedown.md`.
- Drill ownership and quarterly cadence align to SRE responsibilities in `docs/reliability/dr-policy.md` and runbook ownership in `docs/operations/runbook-overview.md`.
