# Tabletop Drill Evidence — ServiceDown SEV-0

- **Date (UTC):** 2026-05-12
- **Scenario:** Complete platform outage (`ServiceDown`)
- **Facilitator:** SRE (`@vf-sre-leadership`)
- **Participants:** Platform on-call (`@vf-eng-oncall`), Incident commander (`@vf-incident-command`), Security lead (`@vf-security-lead`)

## Objectives

1. Verify PagerDuty + Slack escalation endpoints in runbooks are actionable.
2. Validate handoff from responder channel (`#vf-alerts-critical`) to incident command (`#incident-response`).
3. Confirm SEV-0 executive escalation path through engineering leadership routing.

## Timeline (UTC)

| Time | Event | Evidence |
|------|-------|----------|
| 14:00 | Synthetic `ServiceDown` injected in drill environment | Alertmanager test alert record DRILL-2026-05-12-01 |
| 14:02 | PagerDuty incident opened on `pagerduty-critical` | PagerDuty incident drill reference `PD-DRILL-20260512-001` |
| 14:04 | Notification mirrored into `#vf-alerts-critical` | Slack transcript reference `SLK-DRILL-20260512-A` |
| 14:07 | Incident command moved to `#incident-response` | Slack transcript reference `SLK-DRILL-20260512-B` |
| 14:13 | Executive escalation simulated via `engineering-lead-secondary` | PagerDuty escalation event `PD-ESC-20260512-01` |
| 14:22 | Incident resolved and closed | PagerDuty resolution `PD-DRILL-20260512-001` |

## Findings

- Routing names in runbooks matched active operational conventions and schedule/service names.
- No placeholder escalation strings were used during drill execution.
- Response-time targets met for SEV-0 initial acknowledgment (<5 minutes).

## Follow-ups

- Keep quarterly cadence and attach future drill references in this folder.
- Revalidate naming if PagerDuty schedule aliases or Slack channel conventions change.
