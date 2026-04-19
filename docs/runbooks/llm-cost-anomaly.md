# Runbook: L2HighExtractionCost

## Overview

L2 extraction layer LLM costs have exceeded $10/hour, indicating potential cost anomalies, inefficient extraction jobs, or unexpected usage patterns. This alert helps prevent budget overruns.

## Trigger

- **Alert:** `L2HighExtractionCost`
- **Condition:** `increase(vf_llm_cost_usd_total[1h]) > 10` or `increase(layer2_llm_cost_usd_total[1h]) > 10`
- **Duration:** 5 minutes
- **Dashboard:** [L2 Cost Metrics](../../monitoring/grafana/dashboards/l2-cost-metrics.json)

## Impact

- **Severity:** P3 - Cost anomaly warning
- **Immediate Impact:** Budget consumption accelerated
- **Cascading Impact:** If unaddressed, may hit monthly budget threshold
- **Business Impact:** Increased operational costs

## Diagnosis

### 1. Identify Cost Drivers

```bash
# Check L2 extraction metrics
curl -s "http://localhost:8000/metrics" | grep vf_llm_cost

# Identify which model/provider is consuming most
curl -s "http://prometheus:9090/api/v1/query?query=topk(5, vf_llm_cost_usd_total)"

# Check extraction job status
curl -s "http://layer2-api:8000/v1/extraction/jobs" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.jobs[] | {id, status, cost}'
```

### 2. Analyze Recent Jobs

```bash
# List recent high-cost extractions
kubectl logs -n value-fabric -l app=layer2-extraction --since=1h | \
  grep -i "cost\|tokens\|extraction_complete"

# Check for batch extraction jobs
kubectl get jobs -n value-fabric | grep extraction
```

### 3. Identify Tenant/Source

```bash
# Query by tenant
curl -s "http://prometheus:9090/api/v1/query?query=\"vf_llm_cost_usd_total{tenant_id=~\".*\"}\""
```

## Immediate Containment

### 1. Pause Non-Critical Extractions

```bash
# Pause low-priority extraction jobs
curl -X POST "http://layer2-api:8000/v1/extraction/pause" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"priority": "low", "reason": "cost_control"}'
```

### 2. Adjust Rate Limiting

```bash
# Increase rate limiting for extraction if needed
# Check current rate limits
kubectl exec -n value-fabric deployment/redis -- redis-cli GET "rate_limit:extraction:*"
```

## Remediation

### 1. Optimize Extraction Configuration

```bash
# Review extraction settings
curl -s "http://layer2-api:8000/v1/config/extraction" \
  -H "Authorization: Bearer $API_TOKEN"

# Adjust chunk size (smaller chunks = less cost per call but more calls)
# Adjust model (consider cheaper model for initial extraction)
```

### 2. Review Model Selection

```bash
# Check current model usage distribution
curl -s "http://prometheus:9090/api/v1/query?query=\"sum by (model) (vf_llm_tokens_total)\""

# Consider switching expensive jobs to GPT-4o-mini or Claude Haiku
```

### 3. Root Cause Analysis

```bash
# Find jobs with highest token usage
kubectl logs -n value-fabric -l app=layer2-extraction --since=2h | \
  grep -oP 'tokens_used:\K\d+' | sort -rn | head -20

# Check for extraction loops (same entity extracted multiple times)
kubectl logs -n value-fabric -l app=layer2-extraction | \
  grep -i "retry\|loop\|duplicate"
```

## Validation

```bash
# Verify cost decreasing
watch -n 30 'curl -s http://prometheus:9090/api/v1/query?query="rate(vf_llm_cost_usd_total[5m])"'

# Check alert cleared
kubectl get events -n value-fabric | grep -i "cost"

# Verify extraction still functioning
curl -sf http://layer2-api:8000/health && echo "L2: OK"
```

## Escalation

| Condition | Action |
|-----------|--------|
| Cost > $50/hour | Page platform on-call `#vf-platform-oncall` |
| Cost > $100/hour | Page engineering lead |
| Potential security issue (unauthorized usage) | Engage security `#vf-security-oncall` |

## Prevention

- **Cost budgets:** Set daily/hourly limits in L2 config
- **Model selection:** Use cheaper models for large-scale extraction
- **Batching:** Optimize chunk sizes for cost efficiency
- **Rate limiting:** Implement per-tenant cost quotas
- **Caching:** Cache extraction results for frequently accessed entities

---

**Related Runbooks:**
- [Budget Exceeded](budget-exceeded.md) - Monthly budget threshold
- [Token Spike](token-spike.md) - Token usage anomaly

**External References:**
- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
