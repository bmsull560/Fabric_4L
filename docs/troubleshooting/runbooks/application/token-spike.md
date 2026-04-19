# Runbook: L2TokenUsageSpike

## Overview

L2 extraction layer has consumed over 100K tokens in a 10-minute window, indicating a potential runaway job, extraction loop, or unusually large document processing. This alert helps catch inefficiencies before they become budget issues.

## Trigger

- **Alert:** `L2TokenUsageSpike`
- **Condition:** `increase(vf_llm_tokens_total[10m]) > 100000` or `increase(layer2_llm_tokens_total[10m]) > 100000`
- **Duration:** 5 minutes
- **Dashboard:** [L2 Token Metrics](../../monitoring/grafana/dashboards/l2-token-metrics.json)

## Impact

- **Severity:** P3 - Unusual token consumption
- **Immediate Impact:** Higher costs, potential rate limiting
- **Cascading Impact:** May exhaust API rate limits or quotas
- **Business Impact:** Delayed extractions, increased costs

## Diagnosis

### 1. Identify Token Consumer

```bash
# Check token breakdown by model/provider
curl -s "http://prometheus:9090/api/v1/query?query=\"sum by (model, type) (vf_llm_tokens_total)\""

# Find top consumers
curl -s "http://prometheus:9090/api/v1/query?query=\"topk(5, increase(vf_llm_tokens_total[10m]))\""
```

### 2. Analyze Running Jobs

```bash
# List currently running extraction jobs
curl -s "http://layer2-api:8000/v1/extraction/jobs?status=running" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.jobs[] | {id, source, progress, tokens_used}'

# Check job logs for large inputs
kubectl logs -n value-fabric -l app=layer2-extraction --tail=100 | \
  grep -i "tokens\|large\|chunk\|size"
```

### 3. Detect Loops/Duplicates

```bash
# Check for repeated extractions of same entity
kubectl logs -n value-fabric -l app=layer2-extraction | \
  grep "extracting" | sort | uniq -c | sort -rn | head -20

# Look for retry loops
kubectl logs -n value-fabric -l app=layer2-extraction | \
  grep -i "retry\|attempt\|loop"
```

## Immediate Containment

### 1. Pause Suspicious Jobs

```bash
# Identify job with highest token usage
curl -s "http://layer2-api:8000/v1/extraction/jobs" \
  -H "Authorization: Bearer $API_TOKEN" | \
  jq '.jobs | sort_by(.tokens_used) | reverse | .[0] | .id' -r

# Pause that specific job
curl -X POST "http://layer2-api:8000/v1/extraction/jobs/{job_id}/pause" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"reason": "token_spike_investigation"}'
```

### 2. Check for Infinite Loops

```bash
# Monitor job completion rate
watch -n 5 'kubectl logs -n value-fabric -l app=layer2-extraction --since=1m | wc -l'

# If log count increasing rapidly, likely loop
```

## Remediation

### 1. Fix Extraction Logic

```bash
# Check chunking configuration
kubectl get configmap l2-config -n value-fabric -o yaml | grep -i chunk

# Adjust chunk size (smaller = fewer tokens per call)
kubectl patch configmap l2-config -n value-fabric --patch='{"data":{"CHUNK_SIZE": "2000"}}'
```

### 2. Implement Circuit Breaker

```bash
# Enable extraction circuit breaker
kubectl patch configmap l2-config -n value-fabric --patch='{"data":{"EXTRACTION_CIRCUIT_BREAKER": "true", "MAX_TOKENS_PER_JOB": "50000"}}'

# Restart to apply
kubectl rollout restart deployment/layer2-extraction -n value-fabric
```

### 3. Deduplicate Jobs

```bash
# Check for duplicate extractions
curl -s "http://layer2-api:8000/v1/extraction/jobs" \
  -H "Authorization: Bearer $API_TOKEN" | \
  jq '.jobs | group_by(.source_url) | map(select(length > 1)) | flatten | .[].id'

# Cancel duplicates
curl -X DELETE "http://layer2-api:8000/v1/extraction/jobs/{duplicate_job_id}" \
  -H "Authorization: Bearer $API_TOKEN"
```

## Validation

```bash
# Verify token rate decreasing
watch -n 30 'curl -s http://prometheus:9090/api/v1/query?query="rate(vf_llm_tokens_total[5m])" | jq .data.result[0].value[1]'

# Check alert cleared
kubectl get events -n value-fabric | grep -i "token"

# Test normal extraction still works
curl -X POST "http://layer2-api:8000/v1/extraction/test" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"url": "https://example.com/small-doc.pdf", "priority": "low"}'
```

## Escalation

| Condition | Action |
|-----------|--------|
| Token rate > 500K/10min | Page platform on-call `#vf-platform-oncall` |
| Suspected DoS attack | Page security `#vf-security-oncall` |
| Rate limits hit | Page SRE `#vf-sre-oncall` |

## Prevention

- **Token limits:** Set max tokens per job (50K default)
- **Chunking:** Automatic document chunking for large inputs
- **Deduplication:** Prevent duplicate extractions of same URL
- **Progress tracking:** Monitor and alert on stuck jobs
- **Circuit breakers:** Auto-pause after 100K tokens

---

**Related Runbooks:**
- [LLM Cost Anomaly](llm-cost-anomaly.md) - Hourly cost spike
- [Budget Exceeded](budget-exceeded.md) - Monthly budget threshold

**External References:**
- [OpenAI Tokenizer](https://platform.openai.com/tokenizer)
