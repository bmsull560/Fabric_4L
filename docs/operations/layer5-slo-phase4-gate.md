# Layer 5 Ground Truth SLO Definition and Phase 4 Performance Gate

## Purpose

This document defines **predeclared** Service Level Objectives (SLOs), tenant-scale assumptions, reproducible load-test scenarios, and objective pass/fail gates for Layer 5 Ground Truth critical APIs. Phase 4 completion is gated on measured results against these thresholds; post-hoc reinterpretation is not allowed.

## Scope

Critical Layer 5 APIs in scope:

- **Truth list**: `GET /api/v1/truths`
- **Governance summary**: `GET /api/v1/governance/summary`
- **Maturity evaluation**: `POST /api/v1/evaluations`

These routes are documented in the Layer 5 API reference and are treated as tenant-scoped operations.

## Predeclared tenant-scale assumptions

All scenarios and thresholds in this document assume the following steady-state profile:

- **Tenant cardinality**: 200 active tenants in a 24-hour window.
- **Noisy-neighbor budget**: any single tenant may consume up to 15% of total request volume without causing another tenant to breach SLOs.
- **Dataset shape per tenant**:
  - 5,000 truth records (median)
  - 15,000 truth records (p95)
- **Evidence shape** for maturity evaluation:
  - 8 evidence items (median)
  - 30 evidence items (p95)
- **Payload constraints**:
  - Truth list response page size: 50 items
  - Governance summary payload: <= 64 KB JSON
  - Maturity evaluation request payload: <= 256 KB JSON
- **Runtime topology for gate run**:
  - 3 Layer 5 API replicas
  - 1 PostgreSQL primary, no read replica requirement for this gate
  - Shared Redis queue enabled for sync/retry flows

If runtime topology or payload envelopes differ materially, results must be tagged as non-comparable and Phase 4 remains open until a comparable run is produced.

## SLO targets (latency, errors, throughput)

### Truth list (`GET /api/v1/truths`)

- **Latency SLO** (per tenant and global):
  - p50 <= 120 ms
  - p95 <= 300 ms
  - p99 <= 600 ms
- **Availability / error SLO**:
  - Success rate >= 99.9% over 60 minutes
  - 5xx rate <= 0.1%
  - 429 rate <= 1.0% (counted separately; not treated as 5xx)
- **Throughput SLO**:
  - Sustain >= 250 requests/sec aggregate for 15 minutes
  - Sustain >= 8 requests/sec minimum for each of 20 sampled tenants during aggregate peak

### Governance summary (`GET /api/v1/governance/summary`)

- **Latency SLO**:
  - p50 <= 180 ms
  - p95 <= 450 ms
  - p99 <= 900 ms
- **Availability / error SLO**:
  - Success rate >= 99.7% over 60 minutes
  - 5xx rate <= 0.3%
- **Throughput SLO**:
  - Sustain >= 120 requests/sec aggregate for 15 minutes
  - No tenant with >= 2 requests/sec sustained load may exceed p95 latency target for > 3 consecutive minutes

### Maturity evaluation (`POST /api/v1/evaluations`)

- **Latency SLO**:
  - p50 <= 450 ms
  - p95 <= 1,200 ms
  - p99 <= 2,500 ms
- **Availability / error SLO**:
  - Success rate >= 99.5% over 60 minutes
  - 5xx rate <= 0.5%
  - 422 contract-validation errors are excluded from reliability denominator when payload is intentionally invalid in test cases
- **Throughput SLO**:
  - Sustain >= 60 requests/sec aggregate for 15 minutes
  - Sustain >= 30 requests/sec during mixed transition scenario (defined below)

## Reproducible load-test scenarios

All scenarios must be run from versioned test assets in-repo and stored with immutable metadata:

- commit SHA
- UTC timestamp
- environment ID
- scenario file hash
- dataset seed/version

### Scenario A — Baseline mixed critical traffic

Purpose: establish steady-state baseline across all three critical APIs.

Traffic mix:

- 55% truth list
- 25% governance summary
- 20% maturity evaluation

Load profile:

- Ramp: 5 minutes
- Hold: 15 minutes
- Cooldown: 5 minutes
- Target aggregate: 300 RPS

Pass criteria:

- Every API meets its latency, error, and throughput SLOs
- No tenant-isolation breach (zero cross-tenant record leakage)

### Scenario B — Concurrent transitions stress

Purpose: validate behavior during concurrent state transitions that historically amplify lock/contention and retries.

Traffic mix:

- 40% maturity evaluation
- 35% truth list
- 25% governance summary

Transition behavior:

- 25% of maturity-evaluation calls target entities with active workflow-state transitions
- 10% of those transition calls are forced into near-simultaneous updates (same entity + tenant)

Load profile:

- Ramp: 10 minutes
- Hold: 20 minutes
- Target aggregate: 220 RPS

Pass criteria:

- Maturity evaluation p95 <= 1,500 ms under transition pressure
- Overall 5xx <= 0.7% during hold
- Deadlock/timeouts <= 0.2% of total requests
- Retry queue depth returns to pre-test baseline (+/- 10%) within 5 minutes after hold

### Scenario C — Sync retry burst

Purpose: validate resilience during downstream sync retry storms without relaxing API quality expectations.

Traffic mix:

- 50% maturity evaluation
- 30% truth list
- 20% governance summary

Burst behavior:

- Inject retry burst equivalent to 3x normal retry rate for 8 minutes
- Concurrently maintain 180 RPS foreground API traffic

Load profile:

- Warmup: 5 minutes
- Burst window: 8 minutes
- Recovery window: 12 minutes

Pass criteria:

- Foreground API 5xx rate <= 1.0% during burst
- Foreground API p99 latency degradation <= 2.0x pre-burst baseline for each critical API
- Retry success ratio >= 98% by end of recovery window
- No tenant exceeds 2x its own pre-burst p95 latency for > 4 consecutive minutes

### Scenario D — Noisy-tenant fairness test

Purpose: ensure one high-volume tenant does not collapse SLO compliance for others.

Traffic mix:

- Noisy tenant drives 15% of total traffic at bursty pattern
- Remaining traffic spread across at least 30 tenants

Load profile:

- 20-minute hold at 260 RPS aggregate

Pass criteria:

- At least 95% of non-noisy tenants remain within published p95 latency SLOs
- Non-noisy tenants maintain >= 99.5% success rate
- No evidence of cross-tenant data leakage

## Measurement and scoring rules (predeclared)

- Metrics source: OpenTelemetry spans + API gateway counters + database error counters.
- Time window alignment: 60-second buckets with UTC timestamps.
- Percentiles must be calculated from raw request durations, not downsampled pre-aggregates.
- A run is **invalid** if telemetry loss exceeds 1% of expected request count.
- A scenario is **pass** only if all its pass criteria are satisfied.
- Phase 4 performance gate is **pass** only if Scenarios A, B, C, and D all pass in the same environment class.

## Phase 4 completion gate (mandatory)

Phase 4 for Layer 5 is complete only when all conditions below are met:

1. SLO thresholds in this document are frozen before execution.
2. All four scenarios are executed with reproducible artifacts.
3. All scenario pass criteria are met exactly as written.
4. Evidence bundle is attached to release/readiness review.

If any criterion fails, status remains **Phase 4 Open** regardless of ad hoc explanations.

## Required evidence bundle

Attach the following artifacts to the Phase 4 review package:

- Scenario definitions and checksums
- Dataset seed/version and tenant distribution summary
- Raw metrics export (timestamps, latency histograms, status counts)
- Evaluated pass/fail output per scenario
- Incident notes for any retried or aborted run
- Final gate summary with explicit verdict: `PASS` or `OPEN`

## Change control

Any modification to targets, assumptions, or pass/fail criteria in this document requires:

- Change proposal before the next run
- Rationale linked to architecture or product requirement change
- Version bump in this file
- Explicit approval from service owner and reliability owner

No threshold changes may be made after observing a failing run for the same gate cycle.
