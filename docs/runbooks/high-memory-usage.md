# Runbook: HighMemoryUsage

## Overview

Memory utilization exceeding 4GB sustained for 5+ minutes indicates potential memory leak, inefficient caching, or load-related growth. Risk of OOMKill and service disruption.

## Trigger

- **Alert:** `HighMemoryUsage`
- **Condition:** `layerN_memory_usage_bytes / (1024 * 1024 * 1024) > 4` for 5 minutes
- **Dashboard:** [Resource Usage](../../monitoring/grafana/dashboards/resource-usage.json) → Memory panel

## Impact

- **Severity:** P2 - Warning (P1 if >6GB or OOMKill occurs)
- **Immediate Impact:** Garbage collection pressure, degraded response times
- **Cascading Impact:** OOMKill → pod restart → request failures → retry storms
- **Business Impact:** Degraded UX, potential data loss for in-flight requests

## Diagnosis

### 1. Identify Memory-Heavy Pods

```bash
# Top memory consumers by pod
kubectl top pods -n value-fabric --sort-by=memory | head -10

# Memory by container within pods
kubectl top pods -n value-fabric --containers | sort -k4 -hr | head -10

# Check memory limits vs usage
kubectl get pods -n value-fabric -o json | jq '.items[] | select(.status.containerStatuses[].restartCount > 0) | .metadata.name'
```

### 2. Check for OOMKills

```bash
# Find recently OOMKilled pods
kubectl get pods -n value-fabric -o json | jq '.items[] | .status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled") | {pod: .name, reason: .lastState.terminated.reason, exitCode: .lastState.terminated.exitCode}'

# Check pod status
kubectl describe pod -n value-fabric <pod-name> | grep -A5 "Last State"

# Events showing OOMKill
kubectl get events -n value-fabric --field-selector reason=OOMKilled --sort-by='.lastTimestamp'
```

### 3. Application Memory Analysis

```bash
# If Python app: check memory via API (if metrics endpoint available)
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "
import psutil
process = psutil.Process()
print(f'RSS: {process.memory_info().rss / 1024 / 1024:.1f} MB')
print(f'VMS: {process.memory_info().vms / 1024 / 1024:.1f} MB')
"

# Check for memory growth over time
curl -s http://prometheus:9090/api/v1/query?query='rate(container_memory_usage_bytes[5m])'
```

## Immediate Containment

### 1. Restart Affected Pods

```bash
# Identify and restart high-memory pod
kubectl delete pod -n value-fabric <pod-name>

# Or restart entire deployment
kubectl rollout restart deployment/layer4-agents -n value-fabric
kubectl rollout status deployment/layer4-agents -n value-fabric --timeout=120s
```

### 2. Increase Memory Limits (Emergency)

```bash
# Patch deployment to increase memory limit
kubectl patch deployment/layer4-agents -n value-fabric --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value":"8Gi"}]'

# Verify new pods have increased limits
kubectl get pods -n value-fabric -o json | jq '.items[].spec.containers[].resources.limits.memory'
```

### 3. Scale to Distribute Load

```bash
# Scale horizontally to reduce per-pod memory pressure
kubectl scale deployment/layer4-agents -n value-fabric --replicas=5

# Verify load distribution
kubectl top pods -n value-fabric -l app=layer4-agents
```

## Remediation

### Quick Fix: Cache/Cleanup

```bash
# Clear Redis cache if caching is memory-intensive
kubectl exec -n value-fabric -it deployment/redis -- redis-cli FLUSHDB

# Restart with memory profiling enabled
kubectl set env deployment/layer4-agents -n value-fabric MALLOC_ARENA_MAX=2
```

### Root Cause Analysis

```bash
# Check for memory leak patterns (growth over time)
curl -s http://prometheus:9090/api/v1/query?query='increase(container_memory_usage_bytes[1h])'

# Correlate with specific operations
kubectl logs -n value-fabric -l app=layer4-agents --since=30m | grep -E "batch|import|export|large" | head -20

# Check batch job history
kubectl get jobs -n value-fabric --sort-by=.status.startTime
```

## Rollback

If memory increase causes issues:

```bash
# Restore original memory limits
kubectl patch deployment/layer4-agents -n value-fabric --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value":"4Gi"}]'

# Check for pods stuck in OOMKilled loop
kubectl get pods -n value-fabric | grep CrashLoopBackOff
```

## Validation

```bash
# Verify memory usage decreased
kubectl top pods -n value-fabric -l app=layer4-agents

# Check OOMKills stopped
kubectl get events -n value-fabric --field-selector reason=OOMKilled | wc -l

# Verify application responsive
curl -sf https://api.valuefabric.io/v1/health && echo "Health: OK"

# Check memory limit vs usage ratio
kubectl top pod -n value-fabric <pod-name> --containers
```

## Escalation

| Condition | Action |
|-----------|--------|
| Memory >6GB or OOMKill | Page platform on-call `#vf-platform-oncall` |
| Recurring OOMKills | Escalate to application team with memory profile |
| Memory leak suspected | Engage development team for heap dump analysis |
| >30 min to stabilize | Page SRE lead |

## Prevention

- **Memory limits:** Set requests=50%, limits=100% of expected peak
- **GC tuning:** Configure Python `gc.set_threshold()` or Go `GOGC` appropriately
- **Streaming:** Use generators/streams for large payloads, not full in-memory buffering
- **Caching limits:** Set Redis/memory cache TTLs and max memory policies
- **Load testing:** Verify memory stays flat under sustained load
- **Profiling:** Regular memory profiling in CI/CD
- **Alerts:** Warning at 70% limit, critical at 85%

---

**Related Runbooks:**
- [Disk Space Critical](disk-space-critical.md) - Storage exhaustion
- [High CPU Usage](high-cpu-usage.md) - CPU resource issues
- [Service Down](service-down.md) - Complete outage
