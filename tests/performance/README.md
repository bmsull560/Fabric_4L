# Performance Test Suite (k6)

This suite validates critical runtime paths across Layer 2, Layer 3, and Layer 4.

## Covered critical APIs

- **L2**: `POST /v1/extract-and-ingest`
- **L3**: `POST /v1/search/hybrid`
- **L4**: `GET /workflows/active`

## Local execution

```bash
k6 run \
  --summary-export artifacts/performance/k6-summary.json \
  tests/performance/k6/l2_l3_l4_critical_paths.js
```

Optional environment variables:

- `L2_URL`, `L3_URL`, `L4_URL`
- `PERF_DURATION` (default `2m`)
- `L2_RPS`, `L3_RPS`, `L4_RPS`
- `PERF_AUTH_BEARER`, `PERF_TENANT_ID`

## SLO evaluation and regression gate

After the k6 run, evaluate against versioned SLO targets:

```bash
python3 scripts/perf/evaluate_slo.py \
  --summary artifacts/performance/k6-summary.json \
  --slo docs/slo/performance-slo.v1.json \
  --report artifacts/performance/slo-report.md \
  --output artifacts/performance/slo-evaluation.json
```

The script exits non-zero on:

- p95 latency breaches
- error-rate breaches
- regression over the configured threshold

This behavior is used in CI to fail builds when reliability regresses.
