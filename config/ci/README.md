# CI Governance Config

## Required branch protection checks

- **Source of truth:** `required-status-checks.json`
- **Owner:** Platform Governance (with Security co-approval)
- **Change process:**
  1. Update `required-status-checks.json` in the same PR as any CI job rename/add/remove.
  2. Ensure branch protection settings for `main` are updated to match.
  3. Run `python scripts/ci/validate_branch_protection_checks.py --config config/ci/required-status-checks.json --api-response-file <fixture>` in CI/local validation.
  4. Obtain CODEOWNERS approvals from governance owners before merge.

This prevents drift between workflow/job names and repository branch protection enforcement.

## Test skip register governance

- **Source of truth:** `test_skip_register.yaml`
- Entries are normalized by the unique key: `path_pattern + reason_pattern`.
- Duplicate registrations for the same skip condition are not allowed.
- Every skip entry must include exactly one concrete remediation work item under `remediation`:
  - `ticket_id`
  - `due_on`
  - `work_item`

### Fail-closed rule for P0 launch-gated checks

For `severity: P0` and `launch_gate: mandatory` entries in contract/tenant launch checks:

- In CI (`CI=true`), missing prerequisites must **fail** the test (fail-closed).
- Local developer runs may use conditional skip behavior for ergonomics.
- New `pytest.skip` pathways for these checks are not permitted unless they are explicitly local-only and CI-fail-closed.
