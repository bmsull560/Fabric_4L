# Current Launch Readiness (Canonical)

- **Canonical Source:** This document is the single source of truth for launch readiness criteria and percentage.
- **Generated From CI:** `make verify` (lint, type-check, tests, contract tests, build gates) and release-gate evidence scripts.
- **Snapshot Date (UTC):** 2026-05-02
- **Launch Readiness:** **95%**

## CI Evidence Inputs

- `make verify`
- `scripts/release-gate.sh`
- `scripts/render-release-summary.sh`
- `scripts/ci/platform_contract_lint.py`
- `scripts/ci/check_tool_contracts.py`
- `.github/workflows/graph-module-tests.yml` (Graph Query module quality gates on PR + release branches)

## Launch Criteria

The platform is launch-ready when all of the following are true:

1. `make verify` passes with no failing gate.
2. Contract lint + tool contract checks pass.
3. Security smoke tests pass.
4. Graph Query module gate passes on PR and release branches (coverage: lines ≥90%, branches ≥80%, functions ≥90%; flaky rate ≤1.0%; contract and performance jobs green).
5. Release gate report indicates no P0 blockers.
6. Launch readiness percentage remains aligned across canonical docs.

## Historical Snapshot Tagging

Any archived readiness note that includes percentages must include at least one of:

- `Historical Snapshot`
- `Snapshot Date:`
- Filename prefix `ARCHIVED_`

This allows automated checks to distinguish historical records from canonical readiness state.
