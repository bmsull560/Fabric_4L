# Neo4jDown Runbook

> Policy reference: [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md).


## Severity: critical

## Alert Condition
`value_fabric_health_status{component="neo4j"} == 0` for 1 minute.

## Impact
Knowledge graph queries fail. Layer 2 extraction and Layer 3 APIs are degraded or unavailable.

## Triage Steps
1. Check Neo4j pod status: `kubectl get pods -n value-fabric -l app=neo4j`.
2. Review Neo4j logs for OOM, disk, or license errors.
3. Verify network connectivity from dependent services.

## Resolution
### Quick Fix
- Restart the Neo4j pod if it is stuck or OOMKilled.
- Verify memory and disk limits are not exceeded.
- If data corruption is suspected, restore from the latest backup.

### Root Cause Analysis
- Check for recent schema changes or large imports.
- Review resource usage trends (memory, CPU, disk).

## Escalation
- Page the database on-call if restart does not resolve within 5 minutes.
- Contact `#vf-db-oncall`.

## Prevention
- Run Neo4j in a HA or causal cluster in production.
- Monitor disk and memory with predictive alerts.
- Maintain regular automated backups.
