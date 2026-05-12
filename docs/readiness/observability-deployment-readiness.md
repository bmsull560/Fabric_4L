# Observability & Deployment Readiness Evidence

_Last verified: 2026-05-12 (UTC)_

## Scope
This checklist closes ROADMAP Task 46 (Monitoring Stack Completion) and Task 47 (Kubernetes Manifests) P0 verification items.

## Task 46 — Production Observability (P0)

| Check | Status | Verification date | Evidence artifact(s) | Acceptance criteria |
|---|---|---|---|---|
| Prometheus targets healthy for all layers | ✅ PASS | 2026-05-12 | `.github/workflows/k8s-readiness.yml` (Validate Prometheus metrics wiring for all layers), `scripts/ops/monitoring-validation.sh` target query, `monitoring/prometheus/prometheus.yml` scrape config | All layer scrape jobs expose `/metrics`; readiness workflow fails on missing/invalid metrics wiring. |
| Grafana dashboards present and versioned | ✅ PASS | 2026-05-12 | `monitoring/grafana/dashboards/value-fabric-overview.json`, `monitoring/grafana/provisioning/dashboards/value-fabric.yml` | Core platform dashboard JSON exists and is provisioned automatically. |
| Alerting rules deployed and validated | ✅ PASS | 2026-05-12 | `monitoring/alerting/rules.yml`, `scripts/ops/monitoring-validation.sh` rules+alerts checks | Prometheus rule groups load without error; alert API query succeeds. |
| Structured logging with correlation IDs | ✅ PASS | 2026-05-12 | `value_fabric/shared/observability/logging.py`, `value_fabric/shared/observability/probes.py` | JSON structured logs include correlation/request IDs and are available to layers via shared logging utilities. |
| Observability smoke gate | ✅ PASS | 2026-05-12 | `.github/workflows/prod-readiness.yml` (observability-readiness job), `scripts/release-gate.sh` (obs gate) | Release-candidate and mainline profiles require green observability gate execution. |

## Task 47 — Deployment Readiness (P0)

| Check | Status | Verification date | Evidence artifact(s) | Acceptance criteria |
|---|---|---|---|---|
| Kubernetes manifests for L1-L6 + frontend | ✅ PASS | 2026-05-12 | `k8s/base/`, `k8s/deployments/dev-nginx/`, `k8s/deployments/staging-nginx/`, `k8s/deployments/prod-nginx/` | Deployments/services/config objects are present in version-controlled manifests for all runtime services. |
| Kustomize render + schema/policy validation | ✅ PASS | 2026-05-12 | `.github/workflows/k8s-readiness.yml` (Render deployments, Schema validate, OPA policy checks) | Every supported deployment overlay must render and pass kubeconform + conftest. |
| Kubernetes dry-run health checks | ✅ PASS | 2026-05-12 | `.github/workflows/k8s-readiness.yml` (Client dry-run precheck, Server-side dry-run jobs), `.github/workflows/pr-checks.yml` k8s dry-run job | CI must pass dry-run apply checks before merge/release. |
| Post-deploy smoke validation script | ✅ PASS | 2026-05-12 | `scripts/ci/k8s_postdeploy_smoke.sh`, `.github/workflows/build-deploy.yml` (Run post-deploy smoke tests) | Rollout status and service endpoints pass smoke checks after deploy. |
| Release-tag blocking gate | ✅ PASS | 2026-05-12 | `.github/workflows/release-evidence-bundle.yml` (release-readiness-gate job), `tests/release/test_observability_deployment_readiness.py` | Tag-triggered release evidence workflow fails if any observability/deployment criterion is not PASS with dated evidence. |

## Final state
- Task 46 status: **✅ COMPLETE (verified 2026-05-12)**
- Task 47 status: **✅ COMPLETE (verified 2026-05-12)**
