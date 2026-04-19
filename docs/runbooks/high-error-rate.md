# Runbook: High Error Rate

## Overview

HTTP 5xx error rate is above 5% for more than 5 minutes, indicating service degradation across one or more layers.

## Symptoms

- **Alert:** `HighErrorRate`
- **Dashboard:** [Value Fabric Overview](../../monitoring/grafana/dashboards/value-fabric-overview.json) → Error Rate panel
- **Log Query:**
  ```
  {layer=~"layer1|layer2|layer3|layer4|layer5|layer6"} |= "status_code=5"
  or
  {layer=~"layer1|layer2|layer3|layer4|layer5|layer6"} |= "ERROR\|Exception\|Traceback"
  ```
- **User Impact:** Failed requests, broken functionality, potential data loss for in-flight operations
- **Metrics:**
  - `sum(rate(layerN_http_requests_total{status_code=~"5.."}[5m])) / sum(rate(layerN_http_requests_total[5m])) > 0.05`
  - Layer-specific error rates visible in [SLO Dashboard](../../monitoring/grafana/dashboards/slo-detailed.json)

## Diagnosis

### 1. Identify Affected Layer

```bash
# Query Prometheus for layer with highest 5xx rate
curl -s 'http://prometheus:9090/api/v1/query?query='
'sort_desc(sum by (job)(rate(http_requests_total{status_code=~"5.."}[5m])) / sum by (job)(rate(http_requests_total[5m])))'

# Check layer-specific error rates via Grafana or:
kubectl logs -n value-fabric -l app=layer1-ingestion --tail=100 | grep -c "500"
kubectl logs -n value-fabric -l app=layer2-extraction --tail=100 | grep -c "500"
kubectl logs -n value-fabric -l app=layer3-knowledge --tail=100 | grep -c "500"
kubectl logs -n value-fabric -l app=layer4-agents --tail=100 | grep -c "500"
```

### 2. Inspect Application Logs

```bash
# Get recent error logs from affected layer
LAYER="layer4-agents"  # Replace with affected layer
kubectl logs -n value-fabric -l app=$LAYER --tail=500 | grep -E "ERROR|Traceback|Exception"

# Check for panic or crash messages
kubectl logs -n value-fabric -l app=$LAYER --previous 2>/dev/null | tail -100

# Follow logs in real-time
kubectl logs -n value-fabric -l app=$LAYER -f | grep -E "ERROR|5[0-9][0-9]"
```

### 3. Verify Dependency Health

```bash
# Check all dependency health endpoints
for layer in layer1-ingestion layer2-extraction layer3-knowledge layer4-agents; do
  echo "=== $layer ==="
  kubectl exec -n value-fabric -it deployment/$layer -- \
    curl -s http://localhost:8000/health | jq '.dependencies'
done

# Check specific dependency status
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  curl -s http://localhost:8000/health | jq '.dependencies.postgres, .dependencies.neo4j, .dependencies.redis'
```

### 4. Check Recent Deployments

```bash
# Check rollout history for each layer
kubectl rollout history deployment/layer1-ingestion -n value-fabric
kubectl rollout history deployment/layer2-extraction -n value-fabric
kubectl rollout history deployment/layer3-knowledge -n value-fabric
kubectl rollout history deployment/layer4-agents -n value-fabric

# Check recent deployment timestamps
kubectl get deployments -n value-fabric -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.kubernetes\.io/change-cause}{"\t"}{.status.conditions[?(@.type=="Progressing")].lastUpdateTime}{"\n"}{end}'

# Correlate deployment times with error spike
kubectl logs -n value-fabric -l app=layer4-agents --since=30m | grep -E "Starting up|Shutting down|ERROR" | head -20
```

## Remediation

### Immediate Actions (P0)

1. **Restart Affected Pods (if specific instance unhealthy)**
   ```bash
   # Identify unhealthy pods
   kubectl get pods -n value-fabric --field-selector=status.phase!=Running
   
   # Restart specific pod
   kubectl delete pod -n value-fabric <pod-name>
   
   # Or restart entire deployment
   kubectl rollout restart deployment/layer4-agents -n value-fabric
   
   # Wait for rollout
   kubectl rollout status deployment/layer4-agents -n value-fabric --timeout=120s
   ```

2. **Rollback Bad Deployment (if correlated with recent release)**
   ```bash
   # Check recent revisions
   kubectl rollout history deployment/layer4-agents -n value-fabric
   
   # Rollback to previous revision
   kubectl rollout undo deployment/layer4-agents -n value-fabric
   
   # Or rollback to specific revision
   kubectl rollout undo deployment/layer4-agents -n value-fabric --to-revision=2
   
   # Verify rollback
   kubectl rollout status deployment/layer4-agents -n value-fabric
   ```

3. **Scale Horizontally (if traffic surge)**
   ```bash
   # Check current load
   kubectl top pods -n value-fabric -l app=layer4-agents
   
   # Scale up
   kubectl scale deployment/layer4-agents -n value-fabric --replicas=5
   
   # Or enable HPA
   kubectl autoscale deployment/layer4-agents -n value-fabric \
     --min=3 --max=10 --cpu-percent=70
   ```

### Short-Term Mitigation (P1)

4. **Enable Circuit Breakers**
   ```bash
   # Enable circuit breaker for external calls
   kubectl set env deployment/layer4-agents \
     CIRCUIT_BREAKER_ENABLED=true \
     CIRCUIT_BREAKER_FAILURE_THRESHOLD=5 \
     CIRCUIT_BREAKER_TIMEOUT_MS=5000
   
   # Restart to apply
   kubectl rollout restart deployment/layer4-agents -n value-fabric
   ```

5. **Enable Request Rate Limiting**
   ```bash
   # Reduce rate limits to protect service
   kubectl set env deployment/layer4-agents \
     RATE_LIMIT_REQUESTS_PER_MINUTE=100 \
     RATE_LIMIT_BURST=20
   
   # Restart to apply
   kubectl rollout restart deployment/layer4-agents -n value-fabric
   ```

### Dependency-Specific Fixes

**If Postgres errors:**
- See [PostgreSQL Unreachable](./postgres-unreachable.md)

**If Neo4j errors:**
- See [Neo4j Unreachable](./neo4j-unreachable.md)

**If Redis errors:**
- See [Redis Unreachable](./redis-unreachable.md)

**If LLM API errors:**
- See [LLM Provider Outage](./llm-provider-outage.md)

## Verification

### Confirm Error Rate Recovery

```bash
# Monitor error rate for 5 minutes
for i in {1..10}; do
  echo "=== Check $i ==="
  kubectl logs -n value-fabric -l app=layer4-agents --tail=100 | grep -c "500" || echo "0 errors"
  sleep 30
done

# Check health endpoint
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  curl -s http://localhost:8000/health | jq

# Test API directly
curl -s https://api.value-fabric.io/v1/health | jq

# Monitor Prometheus metrics
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status_code=~"5.."}[5m])' | jq '.data.result[] | {layer: .metric.job, error_rate: .value[1]}'
```

## Escalation

- **If error rate remains >20% for >10 minutes:** Page `vf-platform-oncall` via PagerDuty immediately
- **If data loss suspected:** Escalate to Data Engineering team
- **If security-related errors (auth failures, injection attempts):** Escalate to Security team
- **PagerDuty rotation:** `vf-platform-oncall` schedule
- **Slack channel:** `#vf-platform-oncall`

## Post-Incident Actions

1. Document root cause (deployment bug, dependency failure, traffic spike, resource exhaustion)
2. Update deployment process if bad release was cause
3. Add integration tests for the failing path
4. Review and improve circuit breaker configuration
5. Consider adding canary deployments for critical layers

## Prevention

- Require smoke tests before production deployments
- Implement canary deployments with automated rollback
- Set up circuit breakers for external dependencies
- Improve integration test coverage for critical paths
- Configure predictive alerts (error rate trending up, not just threshold)

## Related Runbooks

- [Service Down](./service-down.md) - If complete service unavailability
- [Slow Queries](./slow-queries.md) - If error rate caused by timeouts
- [Neo4j Unreachable](./neo4j-unreachable.md) - If Neo4j dependency errors
- [PostgreSQL Unreachable](./postgres-unreachable.md) - If Postgres dependency errors

## References

- Layer Health Endpoints: `http://localhost:8000/health`
- Prometheus Query: `rate(http_requests_total{status_code=~"5.."}[5m])`
- SLO Dashboard: [Grafana SLO Detailed](../../monitoring/grafana/dashboards/slo-detailed.json)

---

> **Policy reference:** [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md)
