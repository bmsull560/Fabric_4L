# Runbook: HighCPUUsage

## Overview

CPU utilization exceeding 80% for 10+ minutes indicates high load, inefficient algorithms, or runaway processes. Response times degrade, request queuing increases, and timeouts cascade.

## Trigger

- **Alert:** `HighCPUUsage`
- **Condition:** `layerN_cpu_usage_percent > 80` for 10 minutes
- **Dashboard:** [Resource Usage](../../monitoring/grafana/dashboards/resource-usage.json) → CPU panel

## Impact

- **Severity:** P2 - Warning (P1 if >95% or throttling detected)
- **Immediate Impact:** Slower response times, increased request queuing
- **Cascading Impact:** Timeout cascades, circuit breaker trips, user retries
- **Business Impact:** Degraded UX, increased error rates, potential SLA breach

## Diagnosis

### 1. Identify CPU-Heavy Pods and Nodes

```bash
# Top CPU consumers by pod
kubectl top pods -n value-fabric --sort-by=cpu | head -10

# CPU by node (check for noisy neighbor)
kubectl top nodes

# Check CPU throttling
kubectl get pods -n value-fabric -o json | jq '.items[].status.containerStatuses[] | select(.resources.cpu.throttledSeconds > 0) | {pod: .name, throttled: .resources.cpu.throttledSeconds}'
```

### 2. Analyze CPU Patterns

```bash
# Check if traffic-driven (correlate with request rate)
curl -s http://prometheus:9090/api/v1/query?query='rate(http_requests_total[5m])'

# CPU by layer over time
curl -s http://prometheus:9090/api/v1/query?query='avg(rate(container_cpu_usage_seconds_total[5m])) by (pod)'

# Check for batch jobs or background tasks
kubectl get jobs -n value-fabric --sort-by=.status.startTime
kubectl get cronjobs -n value-fabric
```

### 3. Application Profiling

```bash
# Check process list in affected pod
kubectl exec -n value-fabric -it deployment/layer4-agents -- ps aux --sort=-%cpu | head -10

# Check for hot Python threads (if Python app)
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "
import sys
sys.setrecursionlimit(100)
# Check active thread count
import threading
print(f'Threads: {threading.active_count()}')
"

# Check for infinite loops in logs
kubectl logs -n value-fabric -l app=layer4-agents --tail=100 | grep -E "retry|loop|recursion" | head -10
```

## Immediate Containment

### 1. Horizontal Scaling

```bash
# Scale up immediately
kubectl scale deployment/layer4-agents -n value-fabric --replicas=7

# Verify load distribution
kubectl top pods -n value-fabric -l app=layer4-agents

# Check HPA status
kubectl get hpa -n value-fabric
```

### 2. Restart CPU-Spinning Pods

```bash
# Identify specific pod with anomalous CPU
kubectl top pods -n value-fabric -l app=layer4-agents | sort -k2 -hr | head -1

# Delete the specific pod (replacement will spawn)
kubectl delete pod -n value-fabric <cpu-heavy-pod-name>

# Verify replacement starts
kubectl get pods -n value-fabric -l app=layer4-agents -w
```

### 3. Disable Background Jobs

```bash
# Suspend cronjobs temporarily
kubectl patch cronjobs -n value-fabric data-processing --patch '{"spec": {"suspend": true}}'

# Scale down job workers
kubectl scale deployment/job-worker -n value-fabric --replicas=0

# Resume after incident
kubectl patch cronjobs -n value-fabric data-processing --patch '{"spec": {"suspend": false}}'
```

## Remediation

### Quick Fix: Rate Limiting

```bash
# Enable rate limiting if abuse suspected
kubectl patch configmap feature-flags -n value-fabric --type merge -p '{"data":{"RATE_LIMIT_ENABLED":"true", "RATE_LIMIT_RPS":"100"}}'

# Restart to apply
kubectl rollout restart deployment/layer4-agents -n value-fabric
```

### Root Cause Analysis

```bash
# Correlate with deployments (code change?)
kubectl rollout history deployment/layer4-agents -n value-fabric

# Check for algorithmic issues in recent logs
kubectl logs -n value-fabric -l app=layer4-agents --since=1h | grep -E "processing|calculating|rendering" | wc -l

# Database query load (N+1 queries often cause CPU spikes)
curl -s http://prometheus:9090/api/v1/query?query='rate(postgres_stat_database_xact_commit[5m])'
```

## Rollback

If scaling causes issues:

```bash
# Restore original replica count
kubectl scale deployment/layer4-agents -n value-fabric --replicas=3

# Re-enable background jobs
kubectl patch cronjobs -n value-fabric data-processing --patch '{"spec": {"suspend": false}}'

# Disable rate limiting if not needed
kubectl patch configmap feature-flags -n value-fabric --type merge -p '{"data":{"RATE_LIMIT_ENABLED":"false"}}'
```

## Validation

```bash
# Verify CPU decreased
kubectl top pods -n value-fabric -l app=layer4-agents

# Check response times improved
curl -sf https://api.valuefabric.io/v1/health && echo "Health: OK"
curl -w "@curl-format.txt" -o /dev/null -s https://api.valuefabric.io/v1/health

# Verify no throttling
kubectl get pods -n value-fabric -o json | jq '.items[].status.containerStatuses[].resources.cpu.throttledSeconds // 0'

# Check error rates
kubectl logs -n value-fabric -l app=layer4-agents --since=5m | grep -c "ERROR" || echo "No errors"
```

## Escalation

| Condition | Action |
|-----------|--------|
| CPU >95% or throttling | Page platform on-call `#vf-platform-oncall` |
| No clear cause | Escalate to application team for profiling |
| Suspected DDoS/abuse | Engage security team `#vf-security-oncall` |
| >30 min to resolve | Page engineering lead |

## Prevention

- **HPA:** Configure Horizontal Pod Autoscaler at 70% CPU
- **Profiling:** Regular CPU profiling in CI to catch regressions
- **Rate limiting:** Per-IP and per-user rate limits
- **Caching:** Cache expensive computations
- **Algorithm review:** O(n²) operations on large datasets
- **Circuit breakers:** Fail fast on timeout-prone operations
- **Load testing:** Verify CPU stays <70% at expected peak load

---

**Related Runbooks:**
- [High Memory Usage](high-memory-usage.md) - Memory resource issues
- [Slow Queries](slow-queries.md) - Database performance
- [Service Down](service-down.md) - Complete outage
