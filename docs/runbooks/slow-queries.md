# SlowQueries Runbook

> Policy reference: [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md).


## Severity: warning

## Alert Condition
`histogram_quantile(0.95, sum(rate(layerN_http_request_duration_seconds_bucket[10m])) by (le)) > 2` for 10 minutes.

## Impact
Degraded user experience, timeouts, and potential cascading failures.

## Triage Steps
1. Identify which layer (L1–L4) is showing elevated p95 latency.
2. Check database query performance (Postgres slow query log, Neo4j query log).
3. Verify connection pool saturation.
4. Look for external API latency (OpenAI, Anthropic).

## Resolution
### Quick Fix
- Restart the affected service to clear any stuck connections.
- Scale the service or database replicas horizontally.
- Temporarily disable non-critical background jobs.

### Root Cause Analysis
- Capture and explain the slowest queries using `EXPLAIN ANALYZE`.
- Review index usage and add missing indexes.
- Tune connection pool sizes and query timeouts.

## Escalation
- Page the platform on-call if latency is >10s and rising.
- Contact `#vf-platform-oncall`.

## Prevention
- Add query performance regression tests.
- Index hot query paths proactively.
- Set aggressive query timeouts and circuit breakers.
