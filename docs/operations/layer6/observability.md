# Layer 6 Benchmark Service Observability

## Canonical metrics contract

Layer 6 metric names, labels, and label cardinality limits are defined in a single source-of-truth contract:

- `contracts/observability/layer6-metrics.json`

Dashboards and tests must reference this contract to avoid drift.

## Metric meanings

- `layer6_requests_total`: benchmark API request counter. The `route` label is normalized to route templates and `status_class` is collapsed to bounded values such as `2xx`, `4xx`, and `5xx`.
- `layer6_request_duration_seconds`: benchmark API request latency histogram, emitted with the same normalized `route` and `method` labels as the request counter.
- `layer6_dataset_comparisons_total`: compare-operation outcome counter. `industry` tracks the benchmark domain and `outcome` is intentionally bounded to `success`, `dataset_not_found`, `metric_not_found`, and `invalid_input`.
- `layer6_health_status`: service health gauge keyed by `service="layer6-benchmarks"`.

## SLO indicators

Primary SLO indicators for Layer 6 operations:

1. **Availability indicator**: success share from `layer6_requests_total`, derived from total traffic versus `status_class="5xx"` error traffic.
2. **Latency indicator**: p95 from `layer6_request_duration_seconds` stays within the Layer 6 request SLO target.
3. **Quality indicator**: `layer6_dataset_comparisons_total` failure outcomes remain within the expected compare failure budget.

## Probe interpretation

- `/health` is a liveness-only signal. It should stay green during transient or sustained downstream dependency loss as long as the API process itself is alive.
- `/ready` is the routing and alerting signal for Layer 6 dependency health. Alerting should key off sustained `/ready` failures rather than `/health`.
- When investigating readiness alarms, capture the readiness payload `checks` object before restarting pods so operators can distinguish config, connectivity, and startup-state failures.

## Operational drift diagnosis

- Startup logs emit `service`, `version`, `build_sha`, and `config_fingerprint` on the `layer6.startup` logger.
- `config_fingerprint` is derived from a non-secret runtime configuration snapshot so operators can detect configuration drift between instances without exposing secrets.
- `layer6_build_info` is emitted at startup for scrape-side inspection of the active version/build pair.

## Troubleshooting

1. Run dashboard drift validation:
   - `python scripts/observability/check_layer6_dashboard_metrics.py`
2. Validate the contract still includes all emitted metrics:
   - `pytest services/layer6-benchmarks/tests/test_metrics_contract.py`
3. Confirm startup metadata logs include version/build/fingerprint fields:
   - `pytest services/layer6-benchmarks/tests/test_startup_logging.py`
4. Inspect the metrics endpoint and confirm normalized route labels are present:
   - `curl -s http://localhost:8006/metrics | grep layer6_requests_total`
5. If drift is detected, update `contracts/observability/layer6-metrics.json` first, then update the affected dashboards or alert rules to match the emitted names and labels.
