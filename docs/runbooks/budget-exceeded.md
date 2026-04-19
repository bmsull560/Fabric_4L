# Runbook: L2CostBudgetThreshold

## Overview

The L2 extraction layer has exceeded the monthly cost budget of $1000. This is a critical alert requiring immediate attention to prevent runaway costs and potential service disruption due to budget exhaustion.

## Trigger

- **Alert:** `L2CostBudgetThreshold`
- **Condition:** `vf_llm_cost_usd_total > 1000` or `layer2_llm_cost_usd_total > 1000`
- **Duration:** 1 minute
- **Severity:** Critical
- **Dashboard:** [L2 Cost Metrics](../../monitoring/grafana/dashboards/l2-cost-metrics.json)

## Impact

- **Severity:** P1 - Budget exceeded
- **Immediate Impact:** Risk of service disruption if billing limits hit
- **Cascading Impact:** May trigger auto-shutdown of extraction services
- **Business Impact:** Compliance issues, potential data pipeline delays

## Immediate Response (P0)

### 1. Emergency Cost Control

```bash
# Pause all non-essential extraction jobs
curl -X POST "http://layer2-api:8000/v1/extraction/pause-all" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"reason": "budget_exceeded", "exclude_critical": true}'

# Verify pause applied
kubectl get pods -n value-fabric -l app=layer2-extraction
```

### 2. Check Billing Status

```bash
# Verify actual billing (not just metrics)
curl -s "http://layer2-api:8000/v1/billing/current" \
  -H "Authorization: Bearer $API_TOKEN"

# Check provider billing dashboard
# OpenAI: https://platform.openai.com/usage
# Anthropic: https://console.anthropic.com/settings/costs
```

## Diagnosis

### 1. Cost Breakdown by Time

```bash
# Check daily cost trend
curl -s "http://prometheus:9090/api/v1/query?query=\"increase(vf_llm_cost_usd_total[1d])\""

# Identify when cost spike started
kubectl logs -n value-fabric -l app=layer2-extraction --since=24h | \
  grep -i "extraction_started\|cost:" | head -50
```

### 2. Tenant/Source Analysis

```bash
# Find highest consuming tenant
curl -s "http://prometheus:9090/api/v1/query?query=\"topk(5, sum by (tenant_id) (vf_llm_cost_usd_total))\""

# List active jobs by tenant
curl -s "http://layer2-api:8000/v1/extraction/jobs" \
  -H "Authorization: Bearer $API_TOKEN" | \
  jq '.jobs | group_by(.tenant_id) | map({tenant: .[0].tenant_id, count: length, total_cost: map(.cost) | add})'
```

### 3. Job Analysis

```bash
# Check for stuck/long-running jobs
kubectl get jobs -n value-fabric | grep extraction

# Check job durations
kubectl logs -n value-fabric -l app=layer2-extraction | \
  grep "job_duration\|extraction_time" | sort -k2 -rn | head -20
```

## Remediation

### 1. Throttle Extraction

```bash
# Implement emergency rate limiting
kubectl patch configmap l2-config -n value-fabric --patch='{"data":{"EXTRACTION_RATE_LIMIT": "10"}}'

# Restart to apply
kubectl rollout restart deployment/layer2-extraction -n value-fabric
```

### 2. Switch to Cheaper Models

```bash
# Update default model to GPT-4o-mini
kubectl patch configmap l2-config -n value-fabric --patch='{"data":{"DEFAULT_LLM_MODEL": "gpt-4o-mini"}}'

# Or use local model if available
kubectl patch configmap l2-config -n value-fabric --patch='{"data":{"ENABLE_LOCAL_FALLBACK": "true"}}'
```

### 3. Cancel Running Jobs

```bash
# Get list of running jobs
curl -s "http://layer2-api:8000/v1/extraction/jobs?status=running" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.jobs[].id'

# Cancel non-critical jobs
curl -X DELETE "http://layer2-api:8000/v1/extraction/jobs/{job_id}" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"reason": "budget_exceeded"}'
```

## Validation

```bash
# Confirm cost has stabilized
watch -n 30 'curl -s http://prometheus:9090/api/v1/query?query="vf_llm_cost_usd_total" | jq .data.result[0].value[1]'

# Verify extraction still functioning for critical jobs
curl -sf http://layer2-api:8000/health && echo "L2 Health: OK"

# Check alert cleared
kubectl get events -n value-fabric | grep -i "budget\|cost"
```

## Budget Reset

### Monthly Reset

```bash
# Reset budget counter (beginning of month)
# This is typically automatic via metric reset
curl -X POST "http://layer2-api:8000/v1/billing/reset-counter" \
  -H "Authorization: Bearer $API_TOKEN"

# Resume normal operations
curl -X POST "http://layer2-api:8000/v1/extraction/resume" \
  -H "Authorization: Bearer $API_TOKEN"
```

## Escalation

| Condition | Action |
|-----------|--------|
| Cost > $2000 | Page CFO/finance `#vf-finance-oncall` |
| Cost > $5000 | Page CTO `#vf-executive-oncall` |
| Potential fraud/unauthorized usage | Page security `#vf-security-oncall` |
| Service disruption | Page SRE `#vf-sre-oncall` |

## Prevention

- **Hard limits:** Set API-level spend limits with OpenAI/Anthropic
- **Soft limits:** Alert at 50%, 75%, 90% of budget
- **Auto-throttle:** Reduce rate limits as budget approaches
- **Per-tenant quotas:** Prevent single tenant from consuming all budget
- **Model tiering:** Use cheaper models for bulk extraction
- **Caching:** Aggressive caching of extraction results

---

**Related Runbooks:**
- [LLM Cost Anomaly](llm-cost-anomaly.md) - Hourly cost spike
- [Token Spike](token-spike.md) - Token usage anomaly

**External References:**
- [AWS Cost Anomaly Detection](https://docs.aws.amazon.com/cost-management/latest/userguide/anomaly-detection.html)
