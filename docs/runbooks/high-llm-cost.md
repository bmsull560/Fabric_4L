# Runbook: High LLM Cost Rate

> Policy reference: [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md).


## Alert

**Name:** `HighLLMCostRate`

**Expression:**
```promql
sum(rate(vf_llm_cost_usd_total[1h])) > 50
```

**Severity:** warning

---

## Summary

This alert fires when the aggregated LLM spend across all tenants exceeds **$50/hour** for at least 15 minutes.
When spending exceeds soft tenant budgets, automated guardrails should downgrade model usage and apply short throttling.

---

## Immediate Steps

1. **Open the LLM Costs Dashboard**
   - Navigate to `monitoring/grafana/dashboards/llm-costs.json` (or the deployed Grafana instance).
   - Inspect the *Cost by Tenant* and *Cost by Model* panels to identify the primary contributor.

2. **Identify the Culprit**
   - Run the following PromQL queries to narrow down:
     ```promql
     # Top tenants by cost
     topk(5, sum by (tenant_id) (rate(vf_llm_cost_usd_total[1h])) * 3600)

     # Top models by cost
     topk(5, sum by (model) (rate(vf_llm_cost_usd_total[1h])) * 3600)
     ```

3. **Check for Anomalies**
   - Unexpected traffic spike from a specific tenant?
   - A new or expensive model (e.g., `claude-3-opus`) suddenly dominating usage?
   - A runaway agent loop or workflow retry storm?
   - Repeated guardrail events:
     ```promql
     sum by (tenant_id, action, reason) (increase(vf_llm_budget_guardrail_events_total[1h]))
     ```

---

## Mitigation Actions

| Scenario | Action |
|----------|--------|
| Runaway workflow / retry loop | Pause the offending workflow type via the Layer 4 API and inspect trace logs. |
| Tenant abusing API | Temporarily downgrade the tenant's rate limits or contact the tenant admin. |
| Tenant approaching soft budget cap | Keep traffic flowing on fallback model and enforce throttle (`LLM_BUDGET_THROTTLE_SECONDS`). Notify FinOps and tenant admin. |
| Tenant exceeds hard budget cap | Enforced block for further requests until incident commander approves override. |
| Expensive model overuse | Update the default model routing to a cheaper alternative (e.g., `gpt-4o-mini`) in `layer4-agents/src/config/llm_config.py` or equivalent. |
| Pricing table drift | Verify `LLM_COST_TABLE_PATH` override is up-to-date with current provider rates. |

---

## Post-Incident

- Add a note to the incident tracker with:
  - Root cause
  - Tenant/model breakdown
  - Dollars spent during the spike
- If this recurs, consider lowering the alert threshold or adding a per-tenant cost limit.
- Complete `incident-postmortem-template.md` and include mandatory action-item tracking.
