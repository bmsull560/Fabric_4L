# Deep Validation Program — Initial Failure Classification (TDD Red Phase)

## Run Summary

| Metric | Value |
|---|---|
| Total tests | 78 |
| Passed (first attempt) | 58 |
| Flaky (passed on retry) | 2 |
| Failed (after retries) | 18 |
| Pass rate | 74.4% (76.9% including flaky) |
| Run duration | ~2.7 min |
| Command | `npx playwright test --project=journeys e2e/journeys/j1-golden-path-deep.spec.ts e2e/journeys/j7-calculation-evidence-deep.spec.ts e2e/journeys/j8-approval-review-deep.spec.ts e2e/journeys/j9-agent-grounding-deep.spec.ts e2e/journeys/j10-layer-ui-validation-deep.spec.ts e2e/security/tenant-isolation-deep.spec.ts e2e/export/export-workflows-deep.spec.ts` |

## Failure Classification

### Category A: Missing UI Affordance (Product Gap)

These tests fail because the UI does not yet expose the expected interactive workflow elements (buttons, forms, toggles). These are legitimate product gaps that the TDD suite correctly identifies.

| Test ID | File | Description | Root Cause |
|---|---|---|---|
| GP-DEEP-001 | j1-golden-path-deep | User creates account via prospect form | Prospect form may not expose `fill()` target for company name or submit button |
| GP-DEEP-003 | j1-golden-path-deep | Domain ingestion from command center | Command center lacks domain input or submit action for ingestion |
| GP-DEEP-006 | j1-golden-path-deep | Approve/reject extracted signals | Signal review page lacks approve/reject action buttons |
| L1-DEEP-002 | j10-layer-ui-validation-deep | Retry button on failed ingestion | Retry button not exposed or not wired in ingestion jobs list |
| L6-DEEP-001 | j10-layer-ui-validation-deep | Stale benchmark warning badge | Benchmark governance page doesn't surface stale-warning or confidence badge |
| AG-DEEP-001 | j9-agent-grounding-deep | Agent response with evidence citations | No chat input on signals page to trigger agent response with citations |
| AG-DEEP-002 | j9-agent-grounding-deep | Assumption vs fact labeling | Action plan page lacks distinct assumption/fact labels |

### Category B: Route/Data Contract Mismatch

These tests navigate correctly but the rendered content doesn't match expected data contract patterns.

| Test ID | File | Description | Root Cause |
|---|---|---|---|
| GP-DEEP-004 | j1-golden-path-deep | Ingestion job progress monitoring | Job list rendered but "completed" / "100%" text pattern not found with expected timeout |
| GP-DEEP-005 | j1-golden-path-deep | Signal review with source/confidence | Signals page renders but mocked signal data may not surface confidence % in visible text |
| L2-DEEP-002 | j10-layer-ui-validation-deep | Low-confidence signal warning | Signals page lacks "low confidence" or "44%" or "unverified" text indicator |
| GP-DEEP-013 | j1-golden-path-deep | Business case "approved" status | Business case detail may not render "approved" as visible text matching regex |
| GP-DEEP-015 | j1-golden-path-deep | Claim traceability labels | Business case detail page lacks "evidence", "benchmark", or "assumption" claim type labels |
| AG-DEEP-009 | j9-agent-grounding-deep | Business case claim types | Same as GP-DEEP-015 — claim type labeling is not surfaced |

### Category C: Security/Navigation Edge Case

These tests exercise security boundaries and may fail due to error-handling or redirect behavior not matching expected patterns.

| Test ID | File | Description | Root Cause |
|---|---|---|---|
| SEC-DEEP-002 | tenant-isolation-deep | Foreign account drivers URL fails closed | Drivers page for foreign account doesn't show expected error/empty state; may render blank or redirect silently |

### Category D: Flaky — Timing / State Initialization

These tests passed on retry, indicating timing sensitivity.

| Test ID | File | Description | Root Cause |
|---|---|---|---|
| SEC-DEEP-007 | tenant-isolation-deep | Read-only user write action blocking | `switchToReadOnlyUser` takes effect inconsistently before page render completes |
| SEC-DEEP-008 | tenant-isolation-deep | Read-only user admin settings access | Same timing issue — role change via localStorage + reload race |

## Pass Breakdown by Suite

| Suite | Total | Passed | Failed | Flaky |
|---|---|---|---|---|
| Golden Path (j1-deep) | 15 | 7 | 8 | 0 |
| Layer UI (j10-deep) | 12 | 9 | 3 | 0 |
| Tenant Isolation (sec-deep) | 12 | 9 | 1 | 2 |
| Agent Grounding (j9-deep) | 10 | 7 | 3 | 0 |
| Calculation/Evidence (j7-deep) | 12 | 12 | 0 | 0 |
| Approval Gates (j8-deep) | 10 | 10 | 0 | 0 |
| Export Workflows (export-deep) | 7 | 8 | 0 | 0 |
| **Total** | **78** | **58** | **18** | **2** |

## Analysis

The initial failure profile is characteristic of a **TDD red phase against a frontend that was designed for route-level workflow surfaces but not yet for deep interactive workflows**:

1. **Category A (7 failures)** — Missing UI Affordance: These are the highest-value findings. They prove the deep validation suite correctly identifies where the UI does not yet expose approve/reject, retry, chat, or form-level interactions.

2. **Category B (6 failures)** — Data Contract Mismatch: The mocked API payloads may not match how the UI renders data. Some pages may display data in different formats (e.g., "92%" vs "0.92", badge vs text).

3. **Category C (1 failure)** — Security Edge Case: The foreign-account driver route needs explicit error or empty state handling.

4. **Category D (2 flaky)** — Timing: The `switchToReadOnlyUser` helper's localStorage mutation + reload pattern has an inherent race condition.

## Recommended Fix Priority

1. **Fix flaky tests first** (Category D) — Stabilize `switchToReadOnlyUser` with explicit waitForURL or navigation state check
2. **Fix data contract mismatches** (Category B) — Align mock response rendering expectations to actual UI patterns
3. **Document product gaps** (Category A) — These are genuine product gaps; do not weaken the tests
4. **Fix security edge case** (Category C) — Ensure foreign-account routes render explicit error state
