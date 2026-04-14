# Incident Severity Matrix and On-Call Escalation Policy

## Severity matrix

Use the highest matching severity.

| Severity | Definition | Typical impact | Initial response target | Escalation trigger |
|---|---|---|---|---|
| **SEV-1 (Critical)** | Active production outage or severe degradation affecting core platform capabilities or customer-critical workflows. | Multi-service outage, sustained 5xx surge, data loss risk, security/safety exposure. | Acknowledge within **5 minutes** and begin incident command immediately. | Immediately page primary on-call + backup. Engage incident commander and service owners. |
| **SEV-2 (High)** | Significant degradation with customer impact but partial functionality remains. | Single critical dependency down, high latency/error rate in one major layer, urgent workflow backlog. | Acknowledge within **15 minutes**. | Page primary on-call. Escalate to backup if no acknowledgement by target. |
| **SEV-3 (Medium)** | Limited impact, workaround available, or issue confined to non-critical paths. | Intermittent failures, elevated warning alerts, delayed non-critical jobs. | Acknowledge within **1 hour**. | Notify on-call via ticket/Slack. Escalate if impact expands or persists >4 hours. |
| **SEV-4 (Low)** | Minimal/no user impact; maintenance, hygiene, or informational alerts. | Documentation gaps, noisy alert tuning, cosmetic dashboard issues. | Acknowledge within **1 business day**. | Track in backlog; no paging unless reclassified. |

## On-call escalation policy

### Roles

- **Primary on-call**: first responder, triage owner until handoff.
- **Secondary/backup on-call**: backup responder when primary does not acknowledge in target time.
- **Incident commander (IC)**: required for SEV-1 and SEV-2; coordinates responders and comms.
- **Service owner / subject-matter expert (SME)**: engaged by IC based on affected component.

### Escalation timeline

1. **Alert fires and is classified** using the matrix above.
2. **Primary on-call notified** via paging system.
3. If unacknowledged by target window:
   - escalate to **secondary on-call**,
   - then escalate to **engineering manager / duty manager** after an additional 10 minutes for SEV-1/SEV-2.
4. For **SEV-1**, create an incident channel immediately and post updates every 15 minutes.
5. For **SEV-2**, post updates every 30 minutes.
6. For **SEV-3/SEV-4**, use async updates in ticket/Slack at meaningful milestones.

### Communication standards

- Declare incident state: `Investigating` → `Mitigating` → `Monitoring` → `Resolved`.
- Include current severity, customer impact, owner, and next update time in every status message.
- Reclassify severity whenever impact changes.

## Mapping alert labels to incident severity

Alerting rules may use labels such as `critical` and `warning`. Map them as follows unless explicitly overridden in a runbook:

- `critical` alert label → **SEV-1 or SEV-2** (decide based on blast radius and customer impact).
- `warning` alert label → **SEV-3** by default.
- Informational/noise alerts → **SEV-4**.

## Relationship to runbooks

Runbooks in `docs/runbooks/` provide technical triage and remediation steps. This policy governs:

- severity classification,
- paging and escalation sequence,
- incident communications and role ownership.

When runbook instructions conflict with this policy, follow this policy and capture required runbook updates as a corrective action.
