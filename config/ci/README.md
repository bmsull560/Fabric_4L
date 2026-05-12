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
