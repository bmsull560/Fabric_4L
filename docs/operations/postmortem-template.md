# Standard Incident Postmortem Template

Use this template for all SEV-1 and SEV-2 incidents, and for SEV-3 incidents when requested by service owners.

---

## 1) Incident metadata

- **Incident ID**:
- **Title**:
- **Date (UTC)**:
- **Severity**:
- **Status**: Draft / Final
- **Incident commander**:
- **Primary responder(s)**:
- **Affected systems/layers**:
- **Customer impact summary**:

## 2) Executive summary

- What happened?
- How was customer/platform behavior affected?
- What restored service?

## 3) Timeline (UTC)

| Time | Event |
|---|---|
|  | Detection |
|  | Acknowledgement |
|  | Mitigation started |
|  | Service restored |
|  | Incident resolved |

## 4) Detection and response effectiveness

- **Detection source** (alert, customer report, internal observation):
- **MTTA**:
- **MTTR**:
- **What went well**:
- **What was difficult**:

## 5) Root cause analysis

- **Primary root cause**:
- **Contributing factors**:
- **Why existing controls did not prevent this**:

## 6) Corrective actions

Track all actions to closure.

| Action ID | Type (Preventive/Detective/Process) | Description | Owner | Priority | Due date | Status | Verification |
|---|---|---|---|---|---|---|---|
| CA-001 |  |  |  | High/Med/Low |  | Open/In Progress/Blocked/Done | Test, metric, or audit evidence |

### Corrective action policy

- Every postmortem must include at least one measurable corrective action unless explicitly waived by engineering leadership.
- Action owners must update status weekly until closure.
- Closure requires verification evidence (test coverage, alert validation, runbook update, or metric improvement).

## 7) Follow-up communication

- **Internal stakeholders notified**:
- **External/customer communication (if applicable)**:
- **Linked tracking ticket(s)**:

## 8) Sign-off

- **Author**:
- **Reviewer(s)**:
- **Finalized date**:

---

## Postmortem checklist

- [ ] Severity classification matches incident policy.
- [ ] Timeline includes detection, acknowledgement, mitigation, and resolution.
- [ ] Root cause and contributing factors are clearly documented.
- [ ] Corrective actions have owners and due dates.
- [ ] Relevant runbooks/policies updated.
