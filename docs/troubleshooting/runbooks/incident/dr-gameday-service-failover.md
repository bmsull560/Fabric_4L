# DR Game Day Runbook: Critical Service Failover

## Objective

Validate that Tier 0/Tier 1 service restoration can meet policy RTO/RPO targets using backups, IaC, and standard deployment automation.

## Scenario

Primary environment is unavailable for one critical service and its backing store. Simulate failover and full service restoration in an isolated recovery environment.

## Preconditions

- Approved maintenance window and stakeholder notification sent.
- Incident Commander (IC), SRE, database lead, and service owner assigned.
- Most recent backup inventory confirmed available.
- Access validated for backup store, cluster control plane, and secrets manager.

## Success Criteria

- Service health endpoint returns success.
- Core API smoke tests pass.
- Measured RTO and RPO are within policy targets.
- Evidence log is complete and archived.

## Procedure

1. **Kickoff and timestamp capture**
   - Record game-day start time (`T0`) in evidence template.
   - Confirm simulation boundaries and abort criteria.
2. **Declare simulated disaster state**
   - Mark primary service/dependency unavailable.
   - Freeze non-essential production changes during exercise window.
3. **Provision recovery environment**
   - Apply infrastructure baseline (cluster/namespace/network policy).
   - Verify required secrets and config maps are present.
4. **Restore backing data store**
   - Restore latest valid backup.
   - If required, perform point-in-time recovery to simulated incident timestamp.
5. **Deploy service artifacts**
   - Deploy last known good image/tag.
   - Apply runtime config and dependency endpoints.
6. **Validation checks**
   - Run readiness/liveness checks.
   - Run smoke tests for critical endpoints.
   - Execute data validation query set for consistency.
7. **Measure objectives**
   - Capture `restore_complete_time` and calculate RTO.
   - Capture recovered point timestamp and calculate effective RPO.
8. **Debrief**
   - Document deviations, blockers, and follow-up remediation items.
   - Assign owners and due dates.

## Rollback / Abort Conditions

Abort immediately if any of the following occur:

- Exercise threatens production availability beyond approved scope.
- Backup data appears corrupted or incomplete.
- Security controls are violated during restore activity.

On abort, notify incident channel, restore baseline state, and file postmortem action items.

## Evidence

Record all artifacts using `dr-evidence-log-template.md`, including:

- Logs and command transcripts
- Validation outputs
- RTO/RPO calculations
- Remediation action list
