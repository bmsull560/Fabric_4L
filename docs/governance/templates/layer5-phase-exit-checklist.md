# Layer 5 Phase Exit Checklist Template

> Copy this file per milestone (example: `docs/governance/checklists/layer5-phase2-exit-<milestone>.md`).

## Metadata

- Milestone:
- Phase: (0 / 1 / 2 / 3)
- Release candidate SHA:
- Date (UTC):
- Environment:
- Checklist owner (release manager):

## Required commands (copy exact commands from release-gates doc)

- [ ] `python services/layer5-ground-truth/scripts/check_no_duplicate_modules.py`
- [ ] `pytest tests/contract`
- [ ] `pytest tests/security`
- [ ] `pytest services/layer5-ground-truth/tests/test_cross_tenant_hostile.py`
- [ ] `pytest services/layer5-ground-truth/tests/test_api_tenant_propagation.py`
- [ ] `pytest tests/security/test_tenant_boundary_fails_closed.py`
- [ ] `pytest tests/security/test_cross_tenant_api.py`
- [ ] `pytest tests/security/test_cross_tenant_write.py`
- [ ] `pytest tests/security/test_tenant_context_contract.py`
- [ ] `pytest services/layer5-ground-truth/tests`
- [ ] `make verify`

> Keep only commands required for the selected phase; mark non-applicable commands as N/A and remove before final sign-off.

## Numeric thresholds (fill all applicable values)

- [ ] Unauthorized contract diff count = `0`
- [ ] Open Layer 5 P0 items = `0`
- [ ] Open Layer 5 P1 items without owner/due date = `0`
- [ ] Cross-tenant violation count = `0`
- [ ] Missing-tenant-context fail-open count = `0`
- [ ] Tenant-override acceptance count = `0`
- [ ] Allowed flaky test count threshold met (phase-specific)
- [ ] p95 latency target met for:
  - `GET /api/v1/truths` (<= 400 ms)
  - `POST /api/v1/truths/{truth_id}/validate` (<= 400 ms)
- [ ] Layer 5 release-candidate 5xx error rate < `0.5%`

## Artifact checklist

- [ ] Baseline report path committed/attached:
  - `reports/layer5/contracts/phase0-contract-diff.md`
  - `reports/layer5/security/phase1-tenant-isolation.md`
  - `reports/layer5/quality/phase2-test-evidence.md`
  - `reports/layer5/contracts/phase2-contract-diff.md`
  - `reports/layer5/performance/phase3-latency-baseline.md`
  - `reports/layer5/release/phase3-release-gate-report.md`
- [ ] Issue register updated:
  - `docs/governance/layer5-issue-register.md`
  - `docs/governance/layer5-release-issue-register.md`
- [ ] Blocker cross-reference reviewed:
  - `docs/launch/launch-blocker-register.md`
- [ ] Dashboard links captured:
  - Layer 5 governance overview:
  - Layer 5 tenant isolation:
  - Layer 5 service health:
  - Layer 5 latency:
  - Layer 5 error budget:

## Owner sign-off (required)

- [ ] Contract owner sign-off
  - Name:
  - Date:
  - Decision: PASS / FAIL
  - Notes:

- [ ] Tenant-isolation owner sign-off
  - Name:
  - Date:
  - Decision: PASS / FAIL
  - Notes:

- [ ] Ops owner sign-off
  - Name:
  - Date:
  - Decision: PASS / FAIL
  - Notes:

## Final decision

- Phase result: PASS / FAIL
- Residual risks:
- Waivers (if any; include issue ID, owner, expiry):
- Follow-up actions:
