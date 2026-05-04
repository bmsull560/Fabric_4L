# Release Checklist

Use this checklist for staging and production release approvals.

## Compliance and Control Evidence

- [ ] Confirm the [Compliance Control Matrix](../compliance/control-matrix.md) has current owners, review frequency, and evidence locations.
- [ ] Attach relevant evidence links (CI run, dashboard snapshot, audit query output) to the release ticket.

## Pre-Release Validation

- [ ] Run `make verify` and confirm pass.
- [ ] For agent/skill changes, run `make evals` and confirm pass.
- [ ] Run smoke tests (`scripts/smoke/production_smoke.py`) against the target environment.

## Security and Operations

- [ ] Validate required secrets are set from approved secret manager (no plaintext secrets in repo).
- [ ] Confirm monitoring/alerting dashboards are healthy and on-call handoff is complete.
- [ ] Verify runbooks for active alerts are up-to-date.

## Reliability Approval (Required)

- [ ] Confirm latest `artifacts/performance/slo-report.md` and `artifacts/performance/slo-evaluation.json` are attached to the release ticket.
- [ ] Confirm SLO owner review/sign-off is recorded for impacted layers/services.

## Approval

- [ ] Release Manager sign-off.
- [ ] Security/Compliance sign-off.
- [ ] SRE sign-off.
