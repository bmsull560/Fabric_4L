# Layer 6 health vs readiness runbook

## Endpoint contract

- `GET /health`: process liveness only. Returns `200` when the API process is alive.
- `GET /ready`: dependency readiness. Returns `200` only when critical dependencies are ready; returns `503` with deterministic not-ready payload when degraded.

Readiness checks are explicit and stable:

- `config`: startup settings validation succeeded.
- `neo4j`: graph connectivity check passed.
- `benchmark_store`: repository initialized and seeded datasets are queryable.
- `startup`: no critical startup dependency failure was recorded during service boot.

## Probe policy

- Kubernetes `livenessProbe` must target `/health`.
- Kubernetes `readinessProbe` and `startupProbe` must target `/ready`.

## Alerting expectations

- Alert on sustained readiness failures (`/ready` = 503) because traffic should be drained and operator action is required.
- Liveness failures (`/health` != 200) indicate process-level instability; page immediately if restart loops are detected.
- During dependency outages, expect `/health` to remain green while `/ready` is red. This is expected and prevents unnecessary restarts.

## Operator response

1. If `/health` fails, treat the issue as process liveness or crash-loop instability.
2. If `/ready` fails but `/health` stays green, inspect the `checks` object in the readiness payload first.
3. For `config` failures, correct the deployment environment or secret/config map inputs and restart the pod.
4. For `neo4j` or `benchmark_store` failures, restore dependency connectivity before forcing restarts; repeated restarts will not clear a downstream outage.

## Observability checks

- Layer 6 metrics and label contracts live in `contracts/observability/layer6-metrics.json`.
- Startup drift diagnosis should begin with the `layer6.startup` log record, which includes `version`, `build_sha`, and `config_fingerprint`.
- Dashboard and alert query drift can be checked with `python scripts/observability/check_layer6_dashboard_metrics.py`.
