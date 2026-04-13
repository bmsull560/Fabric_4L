# PostgresDown Runbook

## Severity: critical

## Alert Condition
`layer4_health_status{component="postgres"} == 0` for 1 minute.

## Impact
SQL-dependent services (Layer 1, Layer 4, Layer 5) cannot persist state. Workflows fail.

## Triage Steps
1. Check Postgres pod status and events.
2. Review Postgres logs for connection limit, lock, or crash errors.
3. Verify PVC health and disk space.

## Resolution
### Quick Fix
- Restart the Postgres pod if unresponsive.
- Increase `max_connections` temporarily if the limit is reached.
- Failover to a standby replica if running HA.

### Root Cause Analysis
- Identify connection leaks or long-running transactions.
- Check for disk exhaustion or WAL growth issues.

## Escalation
- Page the database on-call if failover or restart fails.
- Contact `#vf-db-oncall`.

## Prevention
- Use connection pooling (PgBouncer).
- Monitor long-running queries and idle connections.
- Run Postgres in HA with automatic failover.
