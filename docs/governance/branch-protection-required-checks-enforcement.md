# Branch Protection Required Checks Enforcement Evidence

- **Evidence date:** 2026-05-12
- **Policy metadata source:** `docs/governance/branch-protection-required-checks.yml`
- **Validation workflow:** `.github/workflows/branch-protection-validation.yml`
- **Drift guard script:** `scripts/ci/check_required_check_policy.py`
- **Drift guard test:** `tests/ci/test_required_check_policy.py`

## Exact required status check names

The required status checks enforced for `main` and `release/*` are:

1. `mandatory-security-regression`
2. `contract-compliance`
3. `p0-e2e-gate`
4. `prod-readiness`
5. `Layer 5 - Source Contract`
6. `Layer 5 - Tenant Isolation Regression`
7. `Layer 5 - Contract Shape Regression`
8. `make verify`

## Enforcement scope verification

`branch-protection-validation.yml` verifies:

- **Pull-request merge enforcement** by asserting `required_status_checks.strict == true`.
- **Direct push enforcement** by asserting `required_status_checks.contexts` is non-empty and includes required contexts.
- **Branch coverage** by validating `main` plus all existing `release/*` branches discovered through the GitHub Branches API.

## Drift prevention policy

`check_required_check_policy.py` fails when required-check metadata and branch-protection validator diverge, including:

- Required check name list drift.
- Missing `main` or `release/*` branch validation logic.
- Missing strict PR merge enforcement check.
- Missing required status context enforcement check.
