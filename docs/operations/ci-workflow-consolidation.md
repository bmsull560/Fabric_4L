# CI Workflow Consolidation Plan

This inventory defines the current cleanup path for overlapping GitHub Actions workflows. It is intentionally non-destructive: workflows stay enabled until branch protection and replacement proof are confirmed.

## Canonical workflow ownership

| Gate family | Canonical workflow | Notes |
| --- | --- | --- |
| Fast PR validation | `pr-checks.yml` | Primary PR build, test, type, and coverage signal. Keep focused on fast merge-blocking feedback. |
| Security scanning | `security-gates.yml` | Owns SAST and dependency audit coverage such as Bandit and pip-audit. |
| Contract enforcement | `contract-compliance.yml` | Owns OpenAPI drift, platform contract linting, and contract scorecard evidence. |
| Launch evidence | `launch-readiness.yml` | Owns staged launch-readiness evidence once remote execution is proven. |

## Deprecation candidates

| Workflow | Current status | Replacement | Required before disabling |
| --- | --- | --- | --- |
| `test.yml` | Legacy monolithic test workflow. | `pr-checks.yml` plus targeted integration workflows. | Confirm branch protection does not require `Test Suite`; confirm per-layer PR checks cover required tests. |
| `critical-gates.yml` | Overlaps auth coverage, tenant isolation, OpenAPI drift, and config gates. | `security-gates.yml`, `contract-compliance.yml`, and `pr-checks.yml`. | Confirm each matrix gate has an active canonical owner and artifact path. |
| `prod-readiness.yml` | Older production-readiness gate. | `launch-readiness.yml`. | Confirm launch-readiness Stage 1-4 remote execution and artifact upload. |

## Cleanup rules

- Do not delete or disable a workflow in the same PR that only introduces the replacement.
- Do not rename required workflow or job names until branch protection has been updated.
- Remove duplicated checks only from the non-canonical workflow after the canonical workflow has a passing remote run.
- Keep security and contract gates visible; do not hide failures by moving them to optional workflows.
