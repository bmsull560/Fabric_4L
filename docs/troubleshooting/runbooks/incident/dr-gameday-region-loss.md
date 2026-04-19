# DR Game Day Runbook: Region/Account Loss Simulation

## Objective

Validate platform-level resilience by simulating loss of the primary region/account and rebuilding minimum viable service from immutable backups and IaC.

## Scenario

Assume primary region/account is inaccessible. Recover Tier 0/Tier 1 capabilities in alternate region/account using documented recovery procedures.

## Preconditions

- Executive and platform approval for quarterly simulation.
- Secondary region/account access tested.
- IaC baselines are versioned and available.
- Immutable backups verified for required data stores.

## Success Criteria

- Control plane, data plane, and critical APIs are restored in alternate region/account.
- Authentication, observability, and alerting minimum stack operational.
- RTO/RPO measurements documented and compared to policy.
- Gaps have owners and remediation dates.

## Procedure

1. **Initiate simulation**
   - Record `T0` and declared impact scope.
   - Establish communication cadence and war-room owner.
2. **Bootstrap foundational infrastructure**
   - Provision networking, cluster, storage classes, and IAM roles via IaC.
   - Validate baseline security controls (RBAC, encryption, audit logs).
3. **Recover Tier 0 data stores**
   - Restore PostgreSQL and Neo4j backups.
   - Validate data integrity checksums and sample queries.
4. **Recover Tier 1 services**
   - Deploy Layer 3, Layer 4, and Layer 5 services with required configs.
   - Restore Redis snapshots if needed for queue continuity.
5. **Restore observability and ops tooling**
   - Bring up alerting and tracing minimum stack.
   - Ensure paging/webhook integrations are functional.
6. **End-to-end validation**
   - Execute cross-layer smoke tests.
   - Validate one representative ingestion → extraction → knowledge/API flow.
7. **Measure and report**
   - Record recovery completion timestamps and effective data loss window.
   - Compare results to `docs/reliability/dr-policy.md` targets.
8. **Closeout**
   - Produce remediation backlog from observed gaps.
   - File evidence package and notify stakeholders.

## Failure Handling

If required controls cannot be established in the secondary environment:

- Stop progression to data/service restore.
- Log blocker with severity.
- Escalate to security and platform leadership.

## Evidence

Use `dr-evidence-log-template.md` to capture timeline, command evidence, and validation outcomes.
