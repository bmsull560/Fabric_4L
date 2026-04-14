# Internal Risk Register Standard

## 1) Purpose

Define a consistent, auditable risk register structure to track security, privacy, compliance,
operational, and business continuity risks.

## 2) Required Risk Record Fields

| Field | Description |
|---|---|
| Risk ID | Unique identifier (e.g., RISK-2026-001) |
| Risk title | Short descriptive title |
| Domain | Security, Privacy, Compliance, Availability, Third-Party, etc. |
| Description | Statement of risk event and conditions |
| Asset / Process | System, process, or dataset at risk |
| Likelihood | Rated 1-5 |
| Impact | Rated 1-5 |
| Inherent risk score | Likelihood × Impact before controls |
| Existing controls | Current preventive/detective/corrective controls |
| Control owner | Person accountable for control operation |
| Residual risk score | Risk rating after controls |
| Treatment plan | Mitigate, transfer, accept, avoid |
| Treatment actions | Planned tasks with due dates |
| Risk owner | Accountable leader for risk disposition |
| Target date | Date by which treatment is expected |
| Status | Open, monitoring, accepted, closed |
| Last reviewed | Most recent review date |
| Next review due | Scheduled review date |
| Evidence links | Internal tickets, tests, logs, policy references |

## 3) Cadence and Governance

- **Monthly:** Domain owners review open Critical/High risks.
- **Quarterly:** Cross-functional risk committee reviews full register and trend metrics.
- **Annually:** Executive review of top enterprise risks and risk appetite alignment.
- **Event-driven reviews:** Triggered by incidents, audit findings, major architecture changes,
  or regulatory updates.

## 4) Control Owner Expectations

Control owners must:

1. Keep control descriptions and operating procedures current.
2. Maintain objective evidence of control operation.
3. Escalate control failures within 1 business day.
4. Propose corrective actions with measurable completion criteria.

## 5) Example Register Entry Template

| Risk ID | Risk title | Domain | Likelihood | Impact | Inherent risk score | Existing controls | Control owner | Residual risk score | Treatment plan | Risk owner | Target date | Status | Last reviewed | Next review due | Evidence links |
|---|---|---|---:|---:|---:|---|---|---:|---|---|---|---|---|---|---|
| RISK-2026-001 | Incomplete vendor security reviews | Third-Party | 4 | 4 | 16 | Vendor intake checklist; Security sign-off gate | Security Manager | 8 | Mitigate | Head of Security | 2026-06-30 | Open | 2026-04-01 | 2026-05-01 | GRC-123; POL-TRUST-01 |
