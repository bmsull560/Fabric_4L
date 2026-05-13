# Performance Test Suite (k6)

This suite validates critical runtime paths across all layers with comprehensive load testing scenarios.

## Test Scenarios

| Scenario | Purpose | File | Duration |
|----------|---------|------|----------|
| **Critical Paths** | Baseline L2→L3→L4 throughput | `l2_l3_l4_critical_paths.js` | 2m |
| **Stress Test** | Find breaking point | `stress-test.js` | 15m |
| **Spike Test** | Sudden traffic handling | `spike-test.js` | 10m |
| **Soak Test** | Memory leak detection | `soak-test.js` | 8h |
| **Multi-Tenant** | Tenant isolation under load | `multi-tenant.js` | 5m |
| **Formula Evaluation** | L3 formula performance | `formula-evaluation.js` | 5m |
| **Workflow Execution** | L4 workflow lifecycle | `workflow-execution.js` | 10m |
| **Cold Start** | First-request latency after idle/restart | `l2_l3_l4_critical_paths.js` (single-VU warm/cold runs) | ~2m x2 |
| **Large Tenant** | High-cardinality tenant dataset behavior | `multi-tenant.js` (`TENANT_COUNT>=200`) | 10m |
| **Circuit Breaker** | External dependency failure and fast-fail recovery | `tests/chaos/test_external_dependency_failure.py` | ~1m |
| **Autoscaling Readiness** | Load profile to trigger HPA and verify scale behavior | `stress-test.js` + `tests/k8s/test_workload_validation.py` | 15m + 1m |

## Covered Critical APIs

- **L2**: `POST /v1/extract-and-ingest` - Entity extraction pipeline
- **L3**: `POST /v1/search/hybrid` - Semantic + keyword search
- **L3**: `POST /v1/formulas/evaluate` - Formula computation
- **L4**: `GET /workflows/active` - Workflow monitoring
- **L4**: `POST /v1/workflows/execute` - Workflow execution

## Local Execution

### Quick Test (2 minutes)
```bash
k6 run \
  --summary-export artifacts/performance/k6-summary.json \
  tests/performance/k6/l2_l3_l4_critical_paths.js
```

### Stress Test (15 minutes)
```bash
k6 run \
  --summary-export artifacts/performance/stress-summary.json \
  --env L2_URL=http://localhost:8002 \
  --env L3_URL=http://localhost:8003 \
  --env L4_URL=http://localhost:8004 \
  tests/performance/k6/stress-test.js
```

### Spike Test (10 minutes)
```bash
k6 run \
  --summary-export artifacts/performance/spike-summary.json \
  --env L3_URL=http://localhost:8003 \
  tests/performance/k6/spike-test.js
```

### Soak Test (8 hours - for stability validation)
```bash
k6 run \
  --summary-export artifacts/performance/soak-summary.json \
  --env PERF_DURATION=8h \
  tests/performance/k6/soak-test.js
```

### Multi-Tenant Isolation Test
```bash
k6 run \
  --summary-export artifacts/performance/tenant-summary.json \
  --env TENANT_COUNT=50 \
  --env PERF_DURATION=5m \
  tests/performance/k6/multi-tenant.js
```

### Formula Evaluation Performance
```bash
k6 run \
  --summary-export artifacts/performance/formula-summary.json \
  --env L3_URL=http://localhost:8003 \
  tests/performance/k6/formula-evaluation.js
```

### Workflow Execution Lifecycle
```bash
k6 run \
  --summary-export artifacts/performance/workflow-summary.json \
  --env L4_URL=http://localhost:8004 \
  --env PERF_DURATION=10m \
  tests/performance/k6/workflow-execution.js
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `L2_URL` | `http://localhost:8002` | Layer 2 (Extraction) endpoint |
| `L3_URL` | `http://localhost:8003` | Layer 3 (Knowledge) endpoint |
| `L4_URL` | `http://localhost:8004` | Layer 4 (Agents) endpoint |
| `PERF_DURATION` | `2m` | Test duration |
| `PERF_AUTH_BEARER` | - | JWT token for auth |
| `PERF_TENANT_ID` | - | Tenant ID header |
| `TENANT_COUNT` | `50` | Number of tenants (multi-tenant test) |
| `WORKFLOW_TIMEOUT` | `120` | Workflow timeout in seconds |

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

## Targeted scenarios requested by platform validation

### Cold-start check (before and after warmup)
```bash
# Cold run (single VU, short duration)
k6 run \
  --summary-export artifacts/performance/cold-start-cold.json \
  --vus 1 --duration 30s \
  tests/performance/k6/l2_l3_l4_critical_paths.js

# Warm run immediately after
k6 run \
  --summary-export artifacts/performance/cold-start-warm.json \
  --vus 1 --duration 30s \
  tests/performance/k6/l2_l3_l4_critical_paths.js
```

### Large-tenant isolation/performance check
```bash
k6 run \
  --summary-export artifacts/performance/large-tenant-summary.json \
  --env TENANT_COUNT=200 \
  --env PERF_DURATION=10m \
  tests/performance/k6/multi-tenant.js
```

### Circuit-breaker resilience check
```bash
pytest tests/chaos/test_external_dependency_failure.py -k circuit -q
```

### Autoscaling readiness check
```bash
# Generate scaling pressure profile
k6 run \
  --summary-export artifacts/performance/autoscaling-load-summary.json \
  tests/performance/k6/stress-test.js

# Validate workload scaling guardrails in manifests/policies
pytest tests/k8s/test_workload_validation.py -q
```
