# Incident Runbooks

This directory contains runbooks for every alert defined in `monitoring/alerting/rules.yml`.

## Policy links

- Severity matrix and escalation policy: [docs/operations/severity-escalation-policy.md](../operations/severity-escalation-policy.md)
- MTTA/MTTR reporting process: [docs/operations/mtta-mttr-reporting.md](../operations/mtta-mttr-reporting.md)
- Postmortem template and corrective actions: [docs/operations/postmortem-template.md](../operations/postmortem-template.md)

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
| DeploymentSignatureVerification | [deployment-signature-verification.md](deployment-signature-verification.md) | critical |
| ZeroTrustValidation | [zero-trust-validation.md](zero-trust-validation.md) | critical |
| BackupDRDrill | [backup-disaster-recovery.md](backup-disaster-recovery.md) | critical |
| DeploymentRollout | [deployment-rollout-and-rollback.md](deployment-rollout-and-rollback.md) | warning |

## Operations Runbooks

| Runbook | File | Purpose |
|---------|------|---------|
| Backup and Disaster Recovery | [backup-disaster-recovery.md](backup-disaster-recovery.md) | RTO/RPO targets, backup verification, PITR restore procedures |
| Deployment Rollout and Rollback | [deployment-rollout-and-rollback.md](deployment-rollout-and-rollback.md) | Rollout strategies, rollback procedures, canary/blue-green criteria |

## Incident Management Templates

| Template | File | Purpose |
|---|---|---|
| Incident Postmortem Template | [incident-postmortem-template.md](incident-postmortem-template.md) | Mandatory post-incident write-up with action-item tracking |
| SLOBreach | [slo-breach-response.md](slo-breach-response.md) | critical |
