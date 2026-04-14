# Incident Postmortem Template (Mandatory)

> Use this template for every Severity 1/2 production incident. Postmortem publication is required within 5 business days.

## 1) Incident Summary

- **Incident ID:**
- **Date (UTC):**
- **Incident Commander:**
- **Severity:**
- **Impacted Services/Layers:**
- **Customer Impact Summary:**
- **Status:** Open / Mitigated / Resolved / Follow-up in progress

## 2) Timeline (UTC)

| Timestamp | Event | Owner |
|---|---|---|
| YYYY-MM-DD HH:MM | Detection | On-call |
| YYYY-MM-DD HH:MM | Mitigation started | IC |
| YYYY-MM-DD HH:MM | Customer comms posted | Comms lead |
| YYYY-MM-DD HH:MM | Service restored | IC |

## 3) Detection and Response Metrics (Required)

- **MTTA (Mean Time to Acknowledge):**
- **MTTR (Mean Time to Restore):**
- **Time to customer comms:**
- **Did we breach error budget?** Yes / No
- **Error budget consumed by incident:**

## 4) Root Cause Analysis

- **Primary root cause:**
- **Contributing factors:**
- **Why existing controls did not prevent this:**

## 5) What Went Well / Poorly

- **Went well:**
- **Went poorly:**
- **Lucky conditions:**

## 6) Mandatory Action-Item Tracking

> Every incident must include at least one preventive and one detective action item.

| Action ID | Type (Preventive/Detective/Corrective) | Description | Owner | Priority | Due Date | Status | Evidence Link |
|---|---|---|---|---|---|---|---|
| AI-001 | Preventive | | | P0/P1/P2 | YYYY-MM-DD | Open/In progress/Done | |
| AI-002 | Detective | | | P0/P1/P2 | YYYY-MM-DD | Open/In progress/Done | |

### Action-item closure gate

A postmortem is only considered **closed** when:
1. All P0 actions are completed.
2. Any deferred action has documented risk acceptance and VP Eng sign-off.
3. Evidence links are attached for each completed item.

## 7) Verification

- **Runbook updated:** Yes / No (link)
- **Alert thresholds updated:** Yes / No (link)
- **Escalation policy tested:** Yes / No (drill reference)
- **Scorecard updated:** Yes / No (weekly scorecard link)
