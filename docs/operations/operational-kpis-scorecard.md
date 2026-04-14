# Operational KPIs and Weekly Scorecard

## KPI Definitions

### MTTA (Mean Time to Acknowledge)
- **Definition:** Average elapsed time from alert firing to on-call acknowledgement.
- **Formula:** `sum(acknowledge_time - alert_fire_time) / incident_count`
- **Target:**
  - Sev1: <= 5 minutes
  - Sev2: <= 10 minutes

### MTTR (Mean Time to Restore)
- **Definition:** Average elapsed time from incident start to customer-impact restoration.
- **Formula:** `sum(restore_time - incident_start_time) / incident_count`
- **Target:**
  - Sev1: <= 60 minutes
  - Sev2: <= 4 hours

### Error Budget
- **SLO target:** 99.9% monthly availability (43.2 minutes max unavailability/month).
- **Budget consumed (%):**
  - `(downtime_minutes / 43.2) * 100`
- **Operating policy:**
  - < 50% consumed: normal release velocity.
  - 50-80% consumed: require reliability review for high-risk changes.
  - > 80% consumed: freeze non-critical releases until recovery plan approved.

## Weekly Operational Scorecard (Publish Every Monday)

| Week (ISO) | Sev1 Count | Sev2 Count | MTTA (Sev1/Sev2) | MTTR (Sev1/Sev2) | Error Budget Consumed (MTD) | LLM Budget Breaches | Drill Compliance | Notes |
|---|---:|---:|---|---|---:|---:|---|---|
| 2026-W01 | 0 | 1 | 4m / 7m | - / 95m | 12% | 0 | 100% | |

## Data Collection Sources

- Alert timings: Alertmanager webhook events.
- Incident lifecycle: incident ticket timeline.
- Availability/error budget: Prometheus SLI burn-rate dashboard.
- LLM budget events: `vf_llm_budget_guardrail_events_total`.

## Publication Process

1. Compile metrics by Monday 17:00 UTC.
2. Publish scorecard to `docs/operations/scorecards/YYYY/`.
3. Review in weekly operations meeting.
4. Open corrective actions for any KPI misses.
