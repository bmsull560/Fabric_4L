# Runbook: LLM Provider Outage

## Overview

This runbook covers incidents where LLM providers (OpenAI, Anthropic, Azure OpenAI, etc.) become unreachable or experience degraded performance, impacting the extraction and agent layers.

## Symptoms

- **Alert:** `LLMProviderOutage` (if configured) or `HighErrorRate` from extraction layer
- **Dashboard:** [LLM Costs & Performance](../../monitoring/grafana/dashboards/llm-costs.json)
- **Log Query:**
  ```
  {layer="layer2"} |= "LLM request failed"
  or
  {layer="layer4"} |= "completion failed"
  ```
- **User Impact:** Extraction jobs failing, agent responses delayed or failing
- **Metrics:**
  - `layer2_llm_requests_failed_total` rising
  - `layer4_llm_latency_seconds` > 30s
  - `vf_llm_cost_usd_total` dropping (indicating failed requests)

## Diagnosis

### 1. Check LLM Provider Health Status

```bash
# Check OpenAI status
curl https://status.openai.com/api/v2/status.json

# Check Anthropic status
curl https://status.anthropic.com/api/v2/status.json
```

### 2. Verify Layer 2 Extraction Health

```bash
# Check extraction error rate
kubectl exec -it deployment/layer2-extraction -- \
  curl -s http://localhost:8000/health | jq

# Check recent LLM client logs
kubectl logs -l app=layer2-extraction --tail=100 | grep -i "llm\|openai\|anthropic"
```

### 3. Check Fallback Provider Status

```bash
# Verify secondary provider configuration
kubectl get configmap layer2-config -o yaml | grep -A5 "llm_fallback"

# Check which provider is currently active
kubectl logs -l app=layer2-extraction --tail=20 | grep "Using provider"
```

### 4. Review Rate Limiting

```bash
# Check if rate limits are being hit
kubectl logs -l app=layer2-extraction | grep -i "rate limit\|429\|too many requests"

# Check current token usage in dashboard
# Grafana: LLM Costs dashboard → Token Usage panel
```

## Remediation

### Immediate Actions (P0)

1. **Enable Fallback Provider**
   ```bash
   # Switch to backup LLM provider
   kubectl set env deployment/layer2-extraction \
     LLM_PRIMARY_PROVIDER=anthropic \
     LLM_FALLBACK_ENABLED=true

   # Rollout restart to apply
   kubectl rollout restart deployment/layer2-extraction
   ```

2. **Enable Circuit Breaker**
   ```bash
   # Enable circuit breaker to prevent cascading failures
   kubectl set env deployment/layer2-extraction \
     LLM_CIRCUIT_BREAKER_ENABLED=true \
     LLM_CIRCUIT_BREAKER_THRESHOLD=5
   ```

3. **Pause Non-Critical Extraction Jobs**
   ```bash
   # List running extraction jobs
   kubectl exec -it deployment/layer2-extraction -- \
     curl -s http://localhost:8000/api/v1/jobs?status=running | jq '.jobs[].id'

   # Pause batch jobs (preserve queue position)
   kubectl exec -it deployment/layer2-extraction -- \
     curl -X POST http://localhost:8000/api/v1/jobs/pause \
     -H "Content-Type: application/json" \
     -d '{"job_type": "extraction", "reason": "llm_outage"}'
   ```

### Short-Term Mitigation (P1)

4. **Enable Caching for Similar Requests**
   ```bash
   # Increase semantic cache TTL
   kubectl set env deployment/layer2-extraction \
     EXTRACTION_CACHE_TTL_SECONDS=3600

   # Enable aggressive caching mode
   kubectl set env deployment/layer4-agents \
     LLM_RESPONSE_CACHE_MODE=aggressive
   ```

5. **Reduce Extraction Complexity**
   ```bash
   # Switch to faster/cheaper model for non-critical extraction
   kubectl set env deployment/layer2-extraction \
     LLM_MODEL_FAST=gpt-3.5-turbo \
     LLM_MODEL_DETAILED=gpt-4-turbo-preview
   ```

### Provider-Specific Actions

**OpenAI Outage:**
- Switch to Azure OpenAI (if configured)
- Use Anthropic Claude as fallback
- Enable local model inference (if available)

**Anthropic Outage:**
- Switch to OpenAI GPT-4
- Reduce max_tokens to stay within rate limits
- Enable batching for queued requests

**Azure OpenAI Outage:**
- Failover to OpenAI direct endpoint
- Verify regional endpoint availability
- Check VNet connectivity

## Verification

### Confirm Service Recovery

```bash
# Test LLM health endpoint
kubectl exec -it deployment/layer2-extraction -- \
  curl -s http://localhost:8000/health/llm | jq

# Expected output:
# {
#   "status": "healthy",
#   "provider": "anthropic",
#   "latency_ms": 1200,
#   "fallback_active": false
# }

# Resume paused jobs
kubectl exec -it deployment/layer2-extraction -- \
  curl -X POST http://localhost:8000/api/v1/jobs/resume \
  -H "Content-Type: application/json" \
  -d '{"job_type": "extraction"}'

# Monitor extraction success rate for 5 minutes
watch -n 30 'kubectl logs -l app=layer2-extraction --tail=50 | grep -c "extraction_complete"'
```

## Escalation

- **If provider outage exceeds 1 hour:** Escalate to Architecture team for alternative provider onboarding
- **If extraction queue > 1000 jobs:** Escalate to Platform team for horizontal scaling
- **If cost spike detected:** Escalate to FinOps via #finops-alerts Slack channel
- **PagerDuty rotation:** `platform-oncall` schedule

## Post-Incident Actions

1. Document provider outage duration and impact
2. Review fallback effectiveness
3. Update cost attribution for any failover usage
4. Consider adding additional provider to rotation

## Related Runbooks

- [High LLM Cost](./high-llm-cost.md) - If failover causes cost spike
- [Workflow Stalled](./workflow-stalled.md) - If extraction jobs backlog
- [High Error Rate](./high-error-rate.md) - General error handling

## References

- LLM Client Configuration: `services/layer2-extraction/.env.example`
- Provider Status Pages:
  - OpenAI: https://status.openai.com
  - Anthropic: https://status.anthropic.com
  - Azure: https://status.azure.com
