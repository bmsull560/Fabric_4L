# Incident Runbook Coverage Audit — 2026-05-18

## Scope Validated

- `docs/runbooks/operational/`
- `docs/troubleshooting/runbooks/`
- `monitoring/alerting/rules-production.yml`
- `monitoring/alertmanager/alertmanager-production.yml`
- `monitoring/grafana/dashboards/value-fabric-operational.json`
- `monitoring/grafana/dashboards/value-fabric-overview.json`

## Top Incident Coverage Matrix

| Incident Class | Runbook Present | Alert Rule Coverage | Alert Includes Runbook Link | Dashboard Link Present | Notes |
|---|---|---|---|---|---|
| Auth failures/denials | ✅ `enterprise-oidc-sso-incident.md` | ✅ `AuthDeniedSpike` | ✅ Added | ✅ Added | Security-owned path validated |
| Postgres outage/pool exhaustion | ✅ `postgres-unreachable.md` | ✅ `DatabasePoolExhausted` | ✅ Added | ✅ Added | Pool exhaustion mapped to DB reachability runbook |
| Redis outage/backlog | ✅ `redis-unreachable.md` | ⚠️ indirect via queue overload/backlog | ✅ Added on queue backlog alerts | ✅ Added | Add dedicated Redis availability alert in follow-up |
| Neo4j outage | ✅ `neo4j-unreachable.md` | ⚠️ no dedicated Neo4j alert in production rules file | N/A | ✅ Added | Add dedicated Neo4j availability alert in follow-up |
| Workflow stalls | ✅ `agent-workflow-stall.md`, `workflow-stalled.md` | ✅ `CeleryQueueBacklog`, `CeleryWorkerOverload` | ✅ Added | ✅ Added | Layer 4 drill confirms workflow triage path |
| LLM provider outages | ✅ `llm-provider-outage.md` | ✅ `HighLLMCost`, `CriticalLLMCost` proxy signal | ✅ Added | ✅ Added | Add provider-health metric alert in follow-up |

## Alert Routing Template Validation

Validated that Slack templates now expose both:
- `runbook_url`
- `escalation_url`

Validated in:
- receiver text for critical/warning/team channels in production Alertmanager config
- shared Slack template file used by Alertmanager templating

## Escalation Documentation Reference

Canonical escalation doc linked in alert annotations:
- `https://wiki.internal/operations/severity-escalation-policy`

Launch readiness governance and owner/SLA matrix published in:
- `docs/runbooks/operational/launch-ops-signoff-checklist.md`

## Follow-up Items

1. Add explicit `Neo4jUnreachable` production alert rule with runbook URL.
2. Add explicit `RedisUnreachable` production alert rule with runbook URL.
3. Add provider API health-check metric alert (not only cost proxy alerts).
