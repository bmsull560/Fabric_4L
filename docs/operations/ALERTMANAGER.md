# Alertmanager Operations Guide

**Status:** ✅ Deployment Complete  
**Version:** v0.28.1  
**Namespace:** value-fabric  
**Last Updated:** 2026-04-19

---

## Overview

Alertmanager handles alert routing, grouping, and notification delivery for the Value Fabric platform. It integrates with:

- **Slack** — Warning and info alerts to designated channels
- **PagerDuty** — Critical alerts for on-call escalation
- **Webhooks** — Fallback/custom notification endpoints

---

## Architecture

```
Prometheus → Alertmanager → Routing Tree → Notifications
                              │
    ┌─────────────────────────┼─────────────────────────┐
    ▼                         ▼                         ▼
  Slack (warning)       PagerDuty (critical)    Webhook (fallback)
```

### Routing Configuration

| Severity | Destination | Channels |
|----------|-------------|----------|
| `critical` | PagerDuty + Slack | #vf-alerts-critical, PD |
| `warning` | Slack | #vf-alerts-warning |
| `info` | Slack | #vf-alerts-info |
| FormulaApproval | Slack | #vf-formula-approvals |
| LLM Cost | Slack | #vf-finops-alerts |

---

## Deployment

### Prerequisites

1. **Vault Secrets** — Ensure these secrets exist in Vault:
   - `value-fabric/monitoring/slack-webhook-url`
   - `value-fabric/monitoring/pagerduty-integration-key`

2. **External Secrets Operator** — Must be running in cluster

### Deploy

```bash
# Development
kubectl apply -k k8s/overlays/dev

# Production (with External Secrets)
kubectl apply -k k8s/overlays/prod
kubectl apply -f k8s/external-secrets/alertmanager-secrets.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n value-fabric -l app=alertmanager

# Check logs
kubectl logs -n value-fabric -l app=alertmanager --tail=100

# Static validation (configuration only)
./scripts/validate-alertmanager.ps1 -Namespace value-fabric

# Full runtime validation (Task 102) - end-to-end alert testing
./scripts/validate-alertmanager.ps1 -Namespace value-fabric -TestAlert -VerboseValidation

# Runtime validation with silence testing
./scripts/validate-alertmanager.ps1 -Namespace value-fabric -TestAlert -TestSilences

# JSON output for CI integration
./scripts/validate-alertmanager.ps1 -Namespace value-fabric -TestAlert -JsonOutput
```

#### Runtime Validation Checks (Task 102)

When `-TestAlert` is specified, the script performs:

| Check | Description | Pass Criteria |
|-------|-------------|---------------|
| Alert Firing | Trigger synthetic alerts via Prometheus API | Alerts appear in Prometheus and Alertmanager |
| Routing Correctness | Verify alerts route to expected receivers | Critical → PagerDuty, Warning → Slack |
| Notification Delivery | Check notification metrics | Slack webhook reachable, metrics show activity |
| Template Integrity | Verify alert content includes required fields | alertname, severity, runbook_url, namespace present |
| Deduplication & Grouping | Fire duplicate alerts, verify grouping | Alerts grouped, not duplicated |
| Silence Handling | Create/test/remove silences (with `-TestSilences`) | Silences suppress alerts correctly |
| Latency | Measure alert propagation time | < 60s from fire to notification (configurable) |

---

## Configuration

### Files

| File | Purpose |
|------|---------|
| `k8s/base/monitoring-alertmanager.yml` | ConfigMap + Deployment + Service + PVC |
| `k8s/base/alertmanager-secrets.yml` | Secret template (dev) |
| `k8s/external-secrets/alertmanager-secrets.yaml` | ExternalSecret (prod) |
| `k8s/base/network-policies/alertmanager.yml` | Network egress/ingress policies |

### Alertmanager Configuration

The alertmanager.yml configuration includes:

- **Routing Tree** — Routes alerts by severity and alertname
- **Receivers** — Slack, PagerDuty, webhook configurations
- **Inhibition Rules** — Prevents notification storms
- **Templates** — Formatted Slack messages with runbook links

### Secret Keys

The `alertmanager-secrets` secret must contain:

```yaml
slack_webhook_url: "https://hooks.slack.com/services/..."  # Required
pagerduty_integration_key: "..."                           # Required
default_webhook_url: "..."                                # Optional
critical_webhook_url: "..."                                # Optional
```

---

## Operations

### View Alertmanager Status

```bash
# Port-forward to UI
kubectl port-forward svc/alertmanager 9093:9093 -n value-fabric

# Open http://localhost:9093
```

### Test Alert Flow

```bash
# Send test alert via Prometheus API
kubectl port-forward svc/prometheus 9090:9090 -n value-fabric &
curl -X POST http://localhost:9090/api/v1/alerts -H 'Content-Type: application/json' -d '[{
  "labels": {
    "alertname": "TestAlert",
    "severity": "warning",
    "namespace": "value-fabric"
  },
  "annotations": {
    "summary": "Test alert",
    "description": "Testing Alertmanager notification flow",
    "runbook_url": "https://github.com/bmsull560/Fabric_4L/tree/main/docs/runbooks"
  }
}]'
```

### Check Silences

```bash
# List active silences
curl http://localhost:9093/api/v2/silences
```

### Create Silence

```bash
# Silence an alert for maintenance
curl -X POST http://localhost:9093/api/v2/silences -H 'Content-Type: application/json' -d '{
  "matchers": [
    {"name": "alertname", "value": "ServiceDown", "isRegex": false}
  ],
  "startsAt": "2026-04-19T00:00:00Z",
  "endsAt": "2026-04-19T01:00:00Z",
  "createdBy": "ops-team",
  "comment": "Planned maintenance"
}'
```

---

## Troubleshooting

### Alerts Not Firing

1. **Check Prometheus alerts page**
   ```bash
   kubectl port-forward svc/prometheus 9090:9093 -n value-fabric
   # Open http://localhost:9090/alerts
   ```

2. **Verify Alertmanager is UP**
   ```bash
   curl http://localhost:9090/api/v1/targets | grep alertmanager
   ```

3. **Check Alertmanager logs**
   ```bash
   kubectl logs -n value-fabric -l app=alertmanager
   ```

### Slack Notifications Not Arriving

1. **Verify webhook URL**
   ```bash
   kubectl get secret alertmanager-secrets -n value-fabric -o jsonpath='{.data.slack_webhook_url}' | base64 -d
   ```

2. **Test webhook directly**
   ```bash
   curl -X POST https://hooks.slack.com/services/... -d '{"text":"Test message"}'
   ```

3. **Check network policy**
   ```bash
   kubectl get networkpolicy alertmanager-egress -n value-fabric -o yaml
   ```

### PagerDuty Alerts Not Firing

1. **Verify integration key**
   ```bash
   kubectl get secret alertmanager-secrets -n value-fabric -o jsonpath='{.data.pagerduty_integration_key}' | base64 -d
   ```

2. **Check PagerDuty service configuration**
   - Ensure service has a Prometheus integration
   - Verify integration key matches

---

## Runbook Links

| Alert | Runbook |
|-------|---------|
| ServiceDown | [service-down.md](../runbooks/service-down.md) |
| HighErrorRate | [high-error-rate.md](../runbooks/high-error-rate.md) |
| HighLLMCostRate | [llm-cost-anomaly.md](../runbooks/llm-cost-anomaly.md) |
| DependencyHealthDegraded | [neo4j-unreachable.md](../runbooks/neo4j-unreachable.md) |
| AuditWriteFailure | [audit-write-failure.md](../runbooks/audit-write-failure.md) |

---

## Maintenance

### Upgrading Alertmanager

1. Update image tag in `k8s/base/monitoring-alertmanager.yml`
2. Apply changes: `kubectl apply -k k8s/overlays/dev`
3. Verify: `kubectl rollout status deployment/alertmanager -n value-fabric`

### Rotating Secrets

1. Update Vault secrets
2. Trigger ExternalSecret refresh:
   ```bash
   kubectl annotate externalsecret alertmanager-secrets -n value-fabric force-sync=$(date +%s) --overwrite
   ```
3. Restart Alertmanager to pick up new secrets:
   ```bash
   kubectl rollout restart deployment/alertmanager -n value-fabric
   ```

---

## Metrics

Alertmanager exposes metrics at `:9093/metrics`:

| Metric | Description |
|--------|-------------|
| `alertmanager_alerts` | Number of active alerts |
| `alertmanager_alerts_received_total` | Total alerts received |
| `alertmanager_notifications_total` | Total notifications sent |
| `alertmanager_notifications_failed_total` | Failed notifications |
| `alertmanager_silences` | Number of active silences |

---

*See also: [Monitoring Stack](./MONITORING.md)*
