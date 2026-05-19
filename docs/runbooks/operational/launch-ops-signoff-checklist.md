# Launch-Ops Sign-off Checklist

Use this checklist before production launch approval. All owners are explicit and SLAs are measurable.

## Scope

- Incident categories: auth, data stores (Postgres/Redis/Neo4j), workflow stalls, and provider outages.
- Alerting stack: Prometheus alert rules, Alertmanager routing, Slack/PagerDuty templates, and dashboard/runbook linkage.

## Sign-off Owners and SLAs

| Area | Primary Owner | Backup Owner | Response SLA | Escalation SLA | Evidence Required |
|---|---|---|---|---|---|
| Authentication incidents and access-deny spikes | Alex Kim (Security On-call) | Priya Raman (Platform Security) | Acknowledge in 5 minutes | Escalate to Incident Commander in 10 minutes | Last 30-day alert sample + runbook validation |
| Postgres availability and pool exhaustion | Maya Patel (DBRE) | Jordan Lee (Platform SRE) | Acknowledge in 5 minutes | Escalate to DBRE manager in 15 minutes | Alert firing simulation + failover checklist |
| Redis availability and queue health | Jordan Lee (Platform SRE) | Ben Ortiz (Data Platform) | Acknowledge in 5 minutes | Escalate to Incident Commander in 15 minutes | Redis runbook drill log + dashboard screenshots |
| Neo4j availability and query degradation | Ben Ortiz (Data Platform) | Maya Patel (DBRE) | Acknowledge in 10 minutes | Escalate to Graph lead in 20 minutes | Neo4j alert test + query latency panel review |
| Layer 4 workflow stall detection | Nina Flores (Agent Platform) | Jordan Lee (Platform SRE) | Acknowledge in 10 minutes | Escalate to Platform Eng Manager in 20 minutes | Workflow stall drill artifact + remediation steps |
| LLM provider outage and fallback execution | Elena Cruz (AI Platform) | Nina Flores (Agent Platform) | Acknowledge in 10 minutes | Escalate to VP Engineering in 30 minutes | Provider failover test + incident comms template |
| Alert routing and notification templates | Jordan Lee (Platform SRE) | Alex Kim (Security On-call) | Config change reviewed in 1 business day | Emergency route patch in 15 minutes | `amtool check-config` + route walk-through |
| Runbook linkage in alerts/dashboards | Priya Raman (Platform Security) | Elena Cruz (AI Platform) | Missing-link fix in 1 business day | Hotfix in 30 minutes during active incident | Link-audit report |

## Checklist

- [ ] Auth incident alerts include canonical runbook links and ownership labels.
- [ ] Postgres/Redis/Neo4j alerts include runbook links and severity-appropriate routing.
- [ ] Workflow stall and provider outage alerts route to owning team channels and critical escalation paths.
- [ ] Alertmanager templates render `runbook_url` for Slack/PagerDuty messages.
- [ ] Dashboards for on-call include direct runbook links in panel descriptions or dashboard links.
- [ ] One game-day drill completed in the current quarter and evidence attached.
- [ ] Escalation policy reviewed against current on-call roster.
- [ ] Incident Commander handoff procedure tested and documented.

## Approval

| Role | Name | Date | Decision |
|---|---|---|---|
| Incident Commander |  |  | Approve / Block |
| Platform SRE Lead |  |  | Approve / Block |
| Security Lead |  |  | Approve / Block |
| AI Platform Lead |  |  | Approve / Block |
