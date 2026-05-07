# Network Policy Exception Process

Temporary network openings are permitted only when there is a time-bound operational need and no safe immediate alternative.

## Required fields for every exception

1. **Source workload identity** (Kubernetes ServiceAccount and namespace).
2. **Destination identity** (Service name/FQDN, namespace, and port list).
3. **Business reason** and affected user/system impact.
4. **Compensating controls** (for example: mTLS + AuthorizationPolicy principal allowlist).
5. **Owner** (team + on-call alias).
6. **Expiry date** (UTC, hard stop).
7. **Rollback plan** with an exact manifest path to revert.

## Approval workflow

1. Open PR with:
   - policy change
   - this exception metadata in the PR description
   - linked ticket
2. Require approval from:
   - service owner
   - security reviewer
3. Merge only after automated tests in `tests/k8s/` pass.

## Expiry enforcement

- Every temporary opening must include an expiry annotation:
  - `security.valuefabric.io/exception-expiry: YYYY-MM-DD`
- CI must fail once the date is in the past.
- Expired exceptions must be removed in the next business day rollback window.

## Audit cadence

- Weekly review of all active exceptions.
- Monthly report of:
  - count of active exceptions
  - count expired/removed
  - average exception duration
