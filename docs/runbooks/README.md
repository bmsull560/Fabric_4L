# Incident Runbooks

This directory contains runbooks for every alert defined in `monitoring/alerting/rules.yml`.

## Policy links

- Severity matrix and escalation policy: [docs/operations/severity-escalation-policy.md](../operations/severity-escalation-policy.md)
- MTTA/MTTR reporting process: [docs/operations/mtta-mttr-reporting.md](../operations/mtta-mttr-reporting.md)
- Postmortem template and corrective actions: [docs/operations/postmortem-template.md](../operations/postmortem-template.md)

## Runbook Index

| Alert | File | Alert Label | Incident Severity Mapping |
|---|---|---|---|
| HighErrorRate | [high-error-rate.md](high-error-rate.md) | critical | SEV-1 or SEV-2 |
| DiskSpaceLow | [disk-space-low.md](disk-space-low.md) | warning | SEV-3 |
| DiskSpaceCritical | [disk-space-critical.md](disk-space-critical.md) | critical | SEV-1 or SEV-2 |
| DiskInodeExhaustion | [disk-inode-exhaustion.md](disk-inode-exhaustion.md) | warning | SEV-3 |
| SlowQueries | [slow-queries.md](slow-queries.md) | warning | SEV-3 |
| Neo4jDown | [neo4j-down.md](neo4j-down.md) | critical | SEV-1 or SEV-2 |
| PostgresDown | [postgres-down.md](postgres-down.md) | critical | SEV-1 or SEV-2 |
| RedisDown | [redis-down.md](redis-down.md) | warning | SEV-3 |
| WorkflowStalled | [workflow-stalled.md](workflow-stalled.md) | warning | SEV-3 |
| HighMemoryUsage | [high-memory-usage.md](high-memory-usage.md) | warning | SEV-3 |
| HighCPUUsage | [high-cpu-usage.md](high-cpu-usage.md) | warning | SEV-3 |
| FormulaApprovalRequired | [formula-approval.md](formula-approval.md) | warning | SEV-3 |
| HighLLMCost | [high-llm-cost.md](high-llm-cost.md) | warning | SEV-3 |

> Final incident severity is determined by business impact and blast radius per the severity matrix.
