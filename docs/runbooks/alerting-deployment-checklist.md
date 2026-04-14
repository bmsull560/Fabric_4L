# Alerting Deployment Checklist

Use this checklist after deploying monitoring/alerting changes.

## Prerequisites

- [ ] `alertmanager-secrets` is applied with real endpoint values for:
  - `default_webhook_url`
  - `critical_webhook_url`
- [ ] Prometheus and Alertmanager pods are healthy in `value-fabric` namespace.
- [ ] Updated rules/config are loaded (`/-/reload` or pod restart completed).

## Alert Smoke Tests

### 1) Trigger a test alert

- [ ] Port-forward Prometheus:
  ```bash
  kubectl -n value-fabric port-forward svc/prometheus 9090:9090
  ```
- [ ] Create a temporary always-firing alert rule (or use Alertmanager API test payload).
- [ ] Confirm alert enters `firing` state in Prometheus UI (`/alerts`).

### 2) Verify Alertmanager routing

- [ ] Port-forward Alertmanager:
  ```bash
  kubectl -n value-fabric port-forward svc/alertmanager 9093:9093
  ```
- [ ] Confirm alert appears in Alertmanager UI (`/#/alerts`).
- [ ] Confirm route/receiver selection is correct (default vs critical).

### 3) Verify on-call receipt

- [ ] Confirm default-severity test alert reaches team destination.
- [ ] Confirm critical-severity test alert reaches incident/on-call destination.
- [ ] Verify payload includes alert name, severity, summary, and runbook link where present.

### 4) Verify auto-resolve behavior

- [ ] Remove/disable the temporary test condition.
- [ ] Confirm alert transitions from `firing` to `resolved` in Prometheus.
- [ ] Confirm resolved notification is sent by Alertmanager (`send_resolved: true`).
- [ ] Confirm on-call tooling marks incident as resolved/closed.

## Production Rule Sanity Checks

- [ ] Error-rate spike rule can be evaluated against live request metrics.
- [ ] Latency SLO breach rule evaluates p95 latency buckets.
- [ ] Dependency-health rules evaluate `value_fabric_health_status` components.
- [ ] Saturation rules evaluate CPU, memory, and disk-queue metrics.

## Rollback

- [ ] Keep previous ConfigMap and Secret revisions available.
- [ ] If routing is incorrect, rollback monitoring manifests and restart Alertmanager.
- [ ] Re-run smoke tests after rollback/roll-forward.
