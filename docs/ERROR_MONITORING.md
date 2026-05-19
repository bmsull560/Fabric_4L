# Error Monitoring

This page is the launch-facing index for production error monitoring. It does not replace the detailed runbooks or Prometheus rules; it points launch operators to the current sources of truth.

## Primary Signals

| Signal | Source of truth | Launch use |
|---|---|---|
| Service health | [Deployment rollback procedure](troubleshooting/runbooks/infrastructure/deployment-rollback.md) | Confirms each layer is answering its health endpoint before and after traffic changes. |
| Error rate | [High error rate runbook](troubleshooting/runbooks/application/high-error-rate.md) and [production alert rules](../monitoring/alerting/rules-production.yml) | Triggers investigation or rollback when 5xx rate exceeds the approved launch threshold. |
| Latency | [production alert rules](../monitoring/alerting/rules-production.yml) and [SLO dashboard](../monitoring/grafana/dashboards/slo-detailed.json) | Detects sustained p95 or p99 regression after deploy or traffic shift. |
| Memory and restarts | [production alert rules](../monitoring/alerting/rules-production.yml) and [operational dashboard](../monitoring/grafana/dashboards/value-fabric-operational.json) | Detects crash loops, resource pressure, and memory-related instability. |
| Alert routing | [production Alertmanager config](../monitoring/alertmanager/alertmanager-production.yml) | Confirms launch alerts route to the on-call owner and incident channel. |

## Launch Expectations

- Alert receivers must be tested before T-0 traffic shift.
- Dashboards used for sign-off must be captured in the launch evidence bundle with timestamp, release candidate SHA, and operator.
- Rollback decisions must reference observable signals, not anecdotal reports alone.
- Incident notes must include the alert name, affected layer, first-seen time, decision maker, and recovery confirmation.

## Related Runbooks

- [Deployment rollback procedure](troubleshooting/runbooks/infrastructure/deployment-rollback.md)
- [Deployment rollout and rollback runbook](troubleshooting/runbooks/infrastructure/deployment-rollout-and-rollback.md)
- [Final-testing launch checklist](launch/final-testing-launch-checklist.md)
- [Launch blocker register](launch/launch-blocker-register.md)
