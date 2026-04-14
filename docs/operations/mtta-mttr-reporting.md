# MTTA/MTTR Definitions and Monthly Reporting Process

## Metric definitions

### MTTA (Mean Time to Acknowledge)

Average elapsed time from **incident start** to **first acknowledgement by an accountable responder**.

- **Start timestamp**: alert trigger time or first externally visible failure signal (whichever is earlier and recorded).
- **Acknowledge timestamp**: first explicit acknowledgement in paging system, incident channel, or incident record.
- **Formula**: `MTTA = sum(acknowledge_time - start_time) / number_of_incidents`.

### MTTR (Mean Time to Resolve)

Average elapsed time from **incident start** to **service restoration / incident resolution**.

- **Resolve timestamp**: when customer impact is mitigated and incident is marked resolved.
- **Formula**: `MTTR = sum(resolve_time - start_time) / number_of_incidents`.

## Scope and segmentation

Track both metrics at minimum by:

- calendar month,
- severity (SEV-1 to SEV-4),
- affected layer/service,
- business hours vs after-hours.

Exclude planned maintenance and test incidents; include all production incidents with user or platform impact.

## Monthly reporting process

1. **Collect data** (first business day of month)
   - Export incident records from paging/incident tooling.
   - Validate start, acknowledge, and resolve timestamps.
2. **Compute metrics**
   - Calculate MTTA/MTTR overall and by severity.
   - Compare against last 3-month trend.
3. **Review outliers**
   - Identify top 3 longest MTTA and MTTR incidents.
   - Note causes (handoff delays, unclear ownership, runbook gaps, dependency failures).
4. **Publish report**
   - Post summary to operations review doc and engineering channel.
   - Include trend chart and corrective actions.
5. **Action and follow-up**
   - Convert recurring causes into tracked corrective actions.
   - Assign owners and due dates; review status weekly until closed.

## Suggested report template

```markdown
# Incident Metrics Report — <YYYY-MM>

## Headline
- Incident count:
- MTTA (overall):
- MTTR (overall):

## By severity
| Severity | Incidents | MTTA | MTTR |
|---|---:|---:|---:|
| SEV-1 |  |  |  |
| SEV-2 |  |  |  |
| SEV-3 |  |  |  |
| SEV-4 |  |  |  |

## Trend vs previous month
- MTTA:
- MTTR:
- Key drivers:

## Corrective actions opened/closed
| Action ID | Description | Owner | Due date | Status |
|---|---|---|---|---|
```

## Targets and review guidance

- Define internal SLO targets for MTTA/MTTR by severity.
- Track percentile metrics (P50/P90) alongside means when sample size allows.
- If two consecutive months miss targets, require an operations improvement plan.
