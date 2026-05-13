# Layer 6 health vs readiness runbook

## Endpoint contract

- `GET /health`: process liveness only. Returns `200` when the API process is alive.
- `GET /ready`: dependency readiness. Returns `200` only when critical dependencies are ready; returns `503` with deterministic not-ready payload when degraded.

## Probe policy

- Kubernetes `livenessProbe` must target `/health`.
- Kubernetes `readinessProbe` and `startupProbe` must target `/ready`.

## Alerting expectations

- Alert on sustained readiness failures (`/ready` = 503) because traffic should be drained and operator action is required.
- Liveness failures (`/health` != 200) indicate process-level instability; page immediately if restart loops are detected.
- During dependency outages, expect `/health` to remain green while `/ready` is red. This is expected and prevents unnecessary restarts.
