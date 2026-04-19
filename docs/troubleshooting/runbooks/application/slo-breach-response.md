# SLO Breach Response Runbook

## Purpose

This runbook defines the closed-loop incident process when performance SLOs are breached by the scheduled load-test pipeline.

## Trigger conditions

A breach is triggered when any of the following occurs in `docs/slo/performance-slo.v1.json` targets:

- p95 latency exceeds the objective threshold.
- Error rate exceeds the objective threshold.
- Regression is above the allowed threshold.

## Incident response steps

1. **Acknowledge the breach** in on-call channel and create an incident ticket.
2. **Link evidence artifacts** from CI:
   - `k6-summary.json`
   - `slo-evaluation.json`
   - `slo-report.md`
3. **Classify impact**:
   - L2 extraction path impact → ingestion/backlog risk.
   - L3 search path impact → graph query latency risk.
   - L4 workflows path impact → orchestration/agent availability risk.
4. **Execute service-specific runbook**:
   - Error dominant failures: `docs/runbooks/high-error-rate.md`
   - Query latency failures: `docs/runbooks/slow-queries.md`
   - Workflow availability failures: `docs/runbooks/workflow-stalled.md`
5. **Implement mitigation** and re-run the load-test workflow manually.
6. **Close loop** by documenting:
   - root cause,
   - mitigation,
   - preventive action,
   - whether SLO baseline/version should be updated.

## Post-incident requirements

- Track the incident in reliability review.
- If objective adjustments are justified, create a version bump (for example `performance-slo.v2.json`) and record rationale.
- Add follow-up tasks to prevent recurrence (capacity, indexing, cache strategy, retries, circuit-breakers).
