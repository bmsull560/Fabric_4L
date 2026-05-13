# Layer 6 Benchmark Service Observability

## Canonical metrics contract

Layer 6 metric names, labels, and label cardinality limits are defined in a single source-of-truth contract:

- `contracts/observability/layer6-metrics.json`

Dashboards and tests must reference this contract to avoid drift.

## Metric meanings

- `layer6_requests_total`: total request count for benchmark API routes partitioned by route/method/status class.
- `layer6_request_duration_seconds`: request latency distribution for benchmark API routes.
- `layer6_dataset_comparisons_total`: count of compare operations by industry and outcome.

## SLO indicators

Primary SLO indicators for Layer 6 operations:

1. **Availability indicator**: non-5xx share from `layer6_requests_total`.
2. **Latency indicator**: p95 from `layer6_request_duration_seconds` stays within route SLO targets.
3. **Quality indicator**: compare outcomes from `layer6_dataset_comparisons_total` stay within expected failure budget.

## Probe interpretation

- `/health` is a liveness-only signal. It should stay green during transient or sustained downstream dependency loss as long as the API process itself is alive.
- `/ready` is the routing and alerting signal for Layer 6 dependency health. Alerting should key off sustained `/ready` failures rather than `/health`.
- When investigating readiness alarms, capture the readiness payload `checks` object before restarting pods so operators can distinguish config, connectivity, and startup-state failures.

## Troubleshooting

1. Run dashboard drift validation:
   - `python scripts/observability/check_layer6_dashboard_metrics.py`
2. Validate the contract still includes all emitted metrics:
   - `pytest services/layer6-benchmarks/tests/test_metrics_contract.py`
3. Confirm startup metadata logs include version/build/fingerprint fields:
   - `pytest services/layer6-benchmarks/tests/test_startup_logging.py`
4. If drift is detected, first update `contracts/observability/layer6-metrics.json`, then update dashboard queries.
