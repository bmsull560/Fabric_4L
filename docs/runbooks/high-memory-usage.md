# HighMemoryUsage Runbook

> Policy reference: [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md).


## Severity: warning

## Alert Condition
`layerN_memory_usage_bytes / (1024 * 1024 * 1024) > 4` for 5 minutes.

## Impact
Risk of OOMKills, degraded performance due to GC pressure, and service restarts.

## Triage Steps
1. Identify the pod(s) with high memory usage.
2. Check memory profiles or heap dumps if available.
3. Look for memory leaks in application logs.

## Resolution
### Quick Fix
- Restart the affected pods to reclaim memory.
- Temporarily increase memory limits.
- Scale horizontally to distribute load.

### Root Cause Analysis
- Analyze heap dumps or memory profiles.
- Correlate memory growth with specific requests or batch jobs.

## Escalation
- Page the platform on-call if OOMKills are recurring.
- Contact `#vf-platform-oncall`.

## Prevention
- Fix memory leaks identified in profiling.
- Set memory limits based on load testing.
- Use streaming instead of in-memory buffering for large payloads.
