# Incident Runbooks

This directory contains runbooks for every alert defined in `monitoring/alerting/rules.yml`.

## Runbook Index

| Alert | File | Severity |
|---|---|---|
| HighErrorRate | [high-error-rate.md](high-error-rate.md) | critical |
| DiskSpaceLow | [disk-space-low.md](disk-space-low.md) | warning |
| DiskSpaceCritical | [disk-space-critical.md](disk-space-critical.md) | critical |
| DiskInodeExhaustion | [disk-inode-exhaustion.md](disk-inode-exhaustion.md) | warning |
| SlowQueries | [slow-queries.md](slow-queries.md) | warning |
| Neo4jDown | [neo4j-down.md](neo4j-down.md) | critical |
| PostgresDown | [postgres-down.md](postgres-down.md) | critical |
| RedisDown | [redis-down.md](redis-down.md) | warning |
| WorkflowStalled | [workflow-stalled.md](workflow-stalled.md) | warning |
| HighMemoryUsage | [high-memory-usage.md](high-memory-usage.md) | warning |
| HighCPUUsage | [high-cpu-usage.md](high-cpu-usage.md) | warning |
| FormulaApprovalRequired | [formula-approval.md](formula-approval.md) | warning |

## Incident Management Templates

| Template | File | Purpose |
|---|---|---|
| Incident Postmortem Template | [incident-postmortem-template.md](incident-postmortem-template.md) | Mandatory post-incident write-up with action-item tracking |
