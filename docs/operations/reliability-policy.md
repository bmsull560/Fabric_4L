# Reliability Policy

## Purpose

This policy standardizes reliability governance for Fabric_4L by defining service-level objectives (SLOs), service-level agreements (SLAs), error budgets, ownership, artifact locations, CI gating, and incident response linkage.

## Scope

Applies to all production services across layers 1-6 and shared platform services (identity and audit).

## Reliability matrix

| Service / Layer | Primary SLO(s) | SLA Commitment | 30d Error Budget | Owner | Escalation Runbook |
|---|---|---|---|---|---|
| Layer 1 Ingestion | 99.9% availability, p99 task enqueue < 5 min | 99.5% monthly uptime | 43m 12s | Data Platform On-Call | `docs/troubleshooting/runbooks/infrastructure/service-down.md` |
| Layer 2 Extraction | 99.5% availability, extraction success >= 98% | 99.0% monthly uptime | 3h 36m | ML Platform On-Call | `docs/troubleshooting/runbooks/application/high-error-rate.md` |
| Layer 3 Knowledge | 99.9% availability, p99 hybrid search < 1s | 99.5% monthly uptime | 43m 12s | Knowledge Graph Team | `docs/troubleshooting/runbooks/infrastructure/neo4j-unreachable.md` |
| Layer 4 Agents | workflow success >= 95%, checkpoint reliability 99.9% | 99.0% monthly uptime | 7h 12m | Agent Runtime Team | `docs/troubleshooting/runbooks/application/workflow-stalled.md` |
| Layer 5 Ground Truth | 99.5% availability, eval pass rate > 85% | 99.0% monthly uptime | 3h 36m | Evaluation Team | `docs/troubleshooting/runbooks/application/stale-ground-truth.md` |
| Layer 6 Benchmarks | 99.0% availability, report generation < 30s | Best effort (internal) | 7h 12m | Perf & Benchmarking | `docs/troubleshooting/runbooks/application/slo-breach-response.md` |
| Shared Identity | auth success >= 99.95%, token validation p99 < 150ms | 99.9% monthly uptime | 21m 36s | Security Platform | `docs/troubleshooting/runbooks/application/zero-trust-validation.md` |
| Shared Audit | append-only write success >= 99.99% | 99.9% monthly uptime | 4m 19s | Compliance Engineering | `docs/troubleshooting/runbooks/application/audit-write-failure.md` |

## SLO artifact standard

Performance SLO evaluation MUST use `scripts/perf/evaluate_slo.py` and publish to:

- `artifacts/performance/k6-summary.json`
- `artifacts/performance/slo-evaluation.json`
- `artifacts/performance/slo-report.md`
- `artifacts/performance/slo-window-history.json` (rolling-window input for CI burn-rate checks)

All CI jobs and manual runs should keep these paths stable to preserve downstream parsing and release evidence linkage.

## CI reliability gate policy

1. Any SLO evaluation breach (`all_passed=false`) fails CI.
2. Burn-rate thresholds are evaluated per service across a rolling window with multi-window policy:
   - short window: 1h burn rate threshold 5x
   - long window: 6h burn rate threshold 2x
3. Breach of either window fails CI and requires incident runbook execution before merge.

## Incident response linkage

When a threshold breach occurs:

1. Trigger `docs/troubleshooting/runbooks/application/slo-breach-response.md`.
2. Follow service-specific runbook from the matrix above.
3. Record incident ID and artifacts in release ticket.

## Review cadence

- Weekly: burn-rate trend review.
- Monthly: SLO/SLA and error-budget review by owners.
- Quarterly: target recalibration and contractual SLA validation.
