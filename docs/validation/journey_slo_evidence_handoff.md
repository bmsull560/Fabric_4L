# Journey SLO Evidence Handoff

This handoff documents the Journey SLO report expected by the launch gate. It prepares the evidence path only; it does not create launch evidence and does not close the Journey SLO gate.

## Gate Purpose

The Journey SLO gate validates the customer-facing launch journey:

```text
account -> signals -> evidence -> driver -> calculator -> business case
```

The gate is implemented in `apps/web/scripts/quality/assert-journey-launch-slos.mjs` and run with:

```powershell
pnpm --dir apps/web run test:journey-slo-gate
```

## Report Path

The gate reads:

- `JOURNEY_SLO_REPORT_PATH`, when set; otherwise
- `tmp/journey-slo-report.json` relative to `apps/web`, which corresponds to `apps/web/tmp/journey-slo-report.json` from the repository root.

Do not hand-write a passing report into `apps/web/tmp/journey-slo-report.json`. That path is reserved for real synthetic monitor output.

## Required Schema

The report must include this journey key:

```json
{
  "account_signals_evidence_driver_calculator_business_case": {
    "successRate": 0.99,
    "p95LatencySeconds": 12,
    "nonEmptyRatio": 1
  }
}
```

The current gate reads only the three numeric fields above. Real evidence must also retain monitor metadata outside the gate-required fields, including release-candidate SHA, monitor run ID, environment, sample count, and measurement window.

A non-evidence schema example is available at:

```text
docs/examples/journey-slo-report.example.json
```

That example is intentionally marked `template_only=true` and `evidence_status=NOT_EVIDENCE`, and its metric values are intentionally failing. It must not be attached as launch evidence.

## Required Thresholds

A real Journey SLO report must prove all of the following over a 15-minute synthetic monitor window:

| Metric | Required threshold |
|---|---:|
| Success rate | `>= 99%` |
| p95 latency | `<= 12s` |
| Non-empty response ratio | `100%` |

The current gate enforces the metric thresholds but does not independently validate the 15-minute window or report provenance. The synthetic monitor job and evidence review must provide that provenance.

## What Counts As Real Evidence

Real Journey SLO evidence must include:

- synthetic monitor output from CI, staging, or another approved production-like environment
- `apps/web/tmp/journey-slo-report.json` or an artifact path referenced by `JOURNEY_SLO_REPORT_PATH`
- command output from `pnpm --dir apps/web run test:journey-slo-gate`
- release-candidate SHA
- monitor run ID and timestamp
- environment name and base URL, with secrets redacted
- sample count and 15-minute measurement window proof
- owner sign-off

## What Does Not Count As Real Evidence

The following must not be treated as launch evidence:

- `docs/examples/journey-slo-report.example.json`
- hand-authored JSON that did not come from a monitor run
- local-only spot checks without a 15-minute window
- mock-enabled runs
- reports without release-candidate SHA
- reports without command output from `test:journey-slo-gate`
- reports with missing or empty journey responses

## CI/Staging Attachment Requirements

Attach these artifacts to the release-candidate evidence bundle:

- Journey SLO report JSON
- `test:journey-slo-gate` command output
- synthetic monitor logs or summary
- release-candidate SHA
- redacted environment metadata
- owner sign-off

If `JOURNEY_SLO_REPORT_PATH` points outside `apps/web/tmp`, record that exact path in the release evidence bundle.

## Status

Journey SLO remains open until real synthetic monitor output exists and `pnpm --dir apps/web run test:journey-slo-gate` passes against that output.

This handoff does not prove production readiness, does not unblock paid GA, and does not close CI/staging reproducibility.
