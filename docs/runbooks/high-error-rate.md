# HighErrorRate Runbook

> Policy reference: [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md).


## Severity: critical

## Alert Condition
`sum(rate(layerN_http_requests_total{status_code=~"5.."}[5m])) / sum(rate(layerN_http_requests_total[5m])) > 0.05` for 5 minutes.

## Impact
Users experience failed requests. Data ingestion, extraction, or agent workflows may be interrupted.

## Triage Steps
1. Check Prometheus or Grafana for the layer with the highest 5xx rate.
2. Inspect application logs for stack traces or panic messages.
3. Verify dependency health (Postgres, Neo4j, Redis, OpenAI).
4. Check recent deployments for correlated code changes.

## Resolution
### Quick Fix
- Restart the affected pods if a specific instance is unhealthy.
- Rollback the most recent deployment if a bad release is suspected.
- Scale the affected layer horizontally if traffic surge is the cause.

### Root Cause Analysis
- Correlate error spikes with deployments, config changes, or infrastructure events.
- Capture and triage representative stack traces in Sentry or logs.
- Review dependency latency and error rates.

## Escalation
- Page the on-call SRE if error rate remains >20% for >10 minutes.
- Contact `#vf-platform-oncall`.

## Prevention
- Require smoke tests and canary deployments.
- Improve integration test coverage for critical paths.
- Set up circuit breakers for external dependencies.
