# Alert Thresholds, Escalation Policy, and Quarterly Drill Verification

## Threshold-to-Escalation Mapping

| Alert | Threshold | Severity | Escalation Policy |
|---|---|---|---|
| HighErrorRate | >5% error rate for 5m | critical | Immediate PagerDuty page (primary), auto-escalate to secondary after 10m |
| ServiceDown | API health=0 for 2m | critical | Immediate PagerDuty page + incident commander assignment |
| HighLLMCostRate | >$50/hour for 15m | warning | Slack warning channel + FinOps on-call notification |
| HighLLMCostCritical | >$100/hour for 10m | critical | PagerDuty page + temporary enforced tenant throttling |

## Quarterly Drill Requirements

- **Frequency:** Once per quarter per alert class (availability, latency, cost).
- **Objective:** Verify thresholds trigger correct channels and escalation paths.
- **Evidence required:**
  - Drill date/time (UTC)
  - Trigger mechanism
  - Alert delivery screenshot/log excerpt
  - Acknowledgement and escalation timestamps
  - Corrective follow-ups

## Quarterly Drill Checklist

| Drill ID | Quarter | Alert Tested | Expected Route | Actual Route | Ack Time | Escalation Time | Pass/Fail | Follow-up |
|---|---|---|---|---|---|---|---|---|
| DRILL-2026Q1-01 | 2026-Q1 | HighErrorRate | PagerDuty+Slack | | | | | |
| DRILL-2026Q1-02 | 2026-Q1 | HighLLMCostCritical | PagerDuty+Throttle | | | | | |

## Failure Policy

If a drill fails:
1. Open a P1 action item in the incident tracker within 1 business day.
2. Patch thresholds/routes and retest within 5 business days.
3. Record remediation in weekly scorecard and next postmortem review.
