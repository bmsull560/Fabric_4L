# Runbook: Redis Unreachable

## Overview

Redis cache is unreachable or reporting unhealthy status, impacting caching, rate limiting, and background task coordination across Layer 1 and Layer 4.

## Symptoms

- **Alert:** `RedisDown`
- **Dashboard:** [Redis Performance](../../monitoring/grafana/dashboards/redis-performance.json)
- **Log Query:**
  ```
  {component="redis"} |= "Connection refused\|LOADING\|MASTERDOWN"
  or
  {layer=~"layer1|layer4"} |= "redis.exceptions.ConnectionError\|Redis is down"
  ```
- **User Impact:** Caching disabled (slower responses), rate limiting may fail, job queuing degraded
- **Metrics:**
  - `layer1_health_status{component="redis"} == 0` or `layer4_health_status{component="redis"} == 0`
  - `redis_connected_clients` dropping
  - Cache hit rate dropping to 0

## Diagnosis

### 1. Check Redis Pod Status

```bash
# Check pod status and events
kubectl get pods -n value-fabric -l app=redis
kubectl describe pod -n value-fabric -l app=redis

# Check for recent restarts
kubectl get pods -n value-fabric -l app=redis \
  -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}'
```

### 2. Verify Redis Logs

```bash
# Check for errors
kubectl logs -n value-fabric -l app=redis --tail=100

# Look for specific error patterns
kubectl logs -n value-fabric -l app=redis | grep -E \
  "ERROR|OOM|Loading|Can't save|MISCONF"

# Check previous container logs if crash looping
kubectl logs -n value-fabric -l app=redis --previous 2>/dev/null | tail -50
```

### 3. Check Memory and Resource Usage

```bash
# Check memory usage
kubectl top pod -n value-fabric -l app=redis

# Check Redis memory stats from inside pod
kubectl exec -n value-fabric -it deployment/redis -- \
  redis-cli INFO memory | grep -E "used_memory|maxmemory|evicted"

# Check current configuration
kubectl exec -n value-fabric -it deployment/redis -- \
  redis-cli CONFIG GET maxmemory

# Check eviction policy
kubectl exec -n value-fabric -it deployment/redis -- \
  redis-cli CONFIG GET maxmemory-policy
```

### 4. Verify Sentinel or Cluster Status (if configured)

```bash
# Check Sentinel status
kubectl get pods -n value-fabric -l app=redis-sentinel

# Get master info from Sentinel
kubectl exec -n value-fabric -it deployment/redis-sentinel-0 -- \
  redis-cli -p 26379 SENTinel master mymaster

# Check if failover has occurred
kubectl exec -n value-fabric -it deployment/redis-sentinel-0 -- \
  redis-cli -p 26379 SENTinel get-master-addr-by-name mymaster

# List replicas
kubectl exec -n value-fabric -it deployment/redis-sentinel-0 -- \
  redis-cli -p 26379 SENTinel replicas mymaster
```

## Remediation

### Immediate Actions (P0)

1. **Restart Redis Pod**
   ```bash
   # Graceful restart
   kubectl rollout restart deployment/redis -n value-fabric
   
   # Wait for readiness
   kubectl wait --for=condition=ready pod -l app=redis -n value-fabric --timeout=60s
   ```

2. **Adjust Memory Limits (if OOMKilled)**
   ```bash
   # Check current limits
   kubectl get deployment redis -n value-fabric -o jsonpath='{.spec.template.spec.containers[0].resources}'
   
   # Increase memory limit
   kubectl set resources deployment/redis -n value-fabric \
     --limits=memory=2Gi --requests=memory=1Gi
   
   # Update maxmemory in Redis config (to be less than container limit)
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli CONFIG SET maxmemory 1536mb
   
   # Restart to apply new limits
   kubectl rollout restart deployment/redis -n value-fabric
   ```

3. **Promote Sentinel Replica (if master is down)**
   ```bash
   # Check current master
   kubectl exec -n value-fabric -it deployment/redis-sentinel-0 -- \
     redis-cli -p 26379 SENTinel get-master-addr-by-name mymaster
   
   # If failover hasn't happened automatically, trigger manual failover
   kubectl exec -n value-fabric -it deployment/redis-sentinel-0 -- \
     redis-cli -p 26379 SENTinel failover mymaster
   
   # Verify new master
   kubectl exec -n value-fabric -it deployment/redis-sentinel-0 -- \
     redis-cli -p 26379 SENTinel get-master-addr-by-name mymaster
   ```

### Short-Term Mitigation (P1)

4. **Enable/Update Eviction Policy**
   ```bash
   # Check current policy
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli CONFIG GET maxmemory-policy
   
   # Set eviction policy (if not already set)
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli CONFIG SET maxmemory-policy allkeys-lru
   
   # For persistent data, use volatile-lru or noeviction
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli CONFIG SET maxmemory-policy volatile-lru
   ```

5. **Clear Large Keys (if memory pressure)**
   ```bash
   # Find largest keys
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli --bigkeys
   
   # List keys by size (if redis-cli --bigkeys not available)
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli EVAL "
     local keys = redis.call('keys', '*')
     local result = {}
     for _,key in ipairs(keys) do
       local size = redis.call('memory', 'usage', key)
       table.insert(result, {key, size})
     end
     return result
     " 0 | head -20
   
   # Delete specific large key if safe
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli DEL "large:key:name"
   ```

6. **Disable Persistence Temporarily (if RDB/AOF causing issues)**
   ```bash
   # Disable RDB snapshots
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli CONFIG SET save ""
   
   # Disable AOF
   kubectl exec -n value-fabric -it deployment/redis -- \
     redis-cli CONFIG SET appendonly no
   
   # Note: Re-enable after recovery if persistence is required
   ```

### Data Recovery (if data loss suspected)

7. **Restore from RDB Backup**
   ```bash
   # Check if backup exists
   kubectl exec -n value-fabric -it deployment/redis-backup -- \
     ls -la /backups/
   
   # Stop Redis
   kubectl scale deployment/redis -n value-fabric --replicas=0
   
   # Restore RDB file
   kubectl cp redis-backup:/backups/dump-$(date +%Y%m%d).rdb \
     value-fabric/redis-0:/data/dump.rdb
   
   # Start Redis
   kubectl scale deployment/redis -n value-fabric --replicas=1
   ```

## Verification

### Confirm Service Recovery

```bash
# Test Redis connectivity
kubectl exec -n value-fabric -it deployment/redis -- \
  redis-cli PING

# Expected output: PONG

# Test from Layer 1
kubectl exec -n value-fabric -it deployment/layer1-ingestion -- \
  python -c "
import redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)
print(f'Redis test: {r.ping()}')
print(f'Set test: {r.set(\"test_key\", \"test_value\")}')
print(f'Get test: {r.get(\"test_key\")}')
r.delete('test_key')
"

# Test from Layer 4
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  python -c "
import redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)
print(f'Redis test: {r.ping()}')
print(f'Info: {r.info()}')
"

# Check health endpoint
kubectl exec -n value-fabric -it deployment/layer1-ingestion -- \
  curl -s http://localhost:8000/health | jq '.dependencies.redis'

# Monitor connection count
kubectl exec -n value-fabric -it deployment/redis -- \
  redis-cli INFO clients | grep connected_clients
```

## Escalation

- **If data loss suspected:** Escalate to Platform on-call immediately
- **If Sentinel failover fails:** Contact Database Architecture team
- **If memory issue persists despite increases:** Review application cache patterns
- **PagerDuty rotation:** `vf-platform-oncall` schedule
- **Slack channel:** `#vf-platform-oncall`

## Post-Incident Actions

1. Document root cause (OOM, memory limit, persistence issue, network)
2. Update memory limits if OOM was cause
3. Review and optimize eviction policy
4. Consider enabling Redis Cluster for HA
5. Review large key patterns and optimize if needed

## Related Runbooks

- [High Memory Usage](./high-memory-usage.md) - If OOM-related
- [High Error Rate](./high-error-rate.md) - If cascading errors
- [Service Down](./service-down.md) - General service recovery

## References

- Redis Documentation: https://redis.io/documentation
- Redis Sentinel Guide: https://redis.io/topics/sentinel
- Redis Kubernetes Config: `k8s/base/redis.yaml`

---

> **Policy reference:** [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md)
