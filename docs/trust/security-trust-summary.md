# Value Fabric Security & Trust Summary

This summary provides a customer-facing overview of our trust posture and where supporting
internal evidence is maintained.

## Core Commitments

- Protect customer data through layered security controls and least-privilege access.
- Operate documented incident response and vulnerability handling workflows.
- Govern third-party risk through structured due diligence and periodic reassessment.
- Provide transparency for data ownership, portability, and deletion commitments.

## Security and Trust Overview

| Area | Customer-facing statement | Internal evidence source(s) |
|---|---|---|
| Access control | Access to production systems and customer data is role-based and reviewed periodically. | IAM access review records; `shared/identity/` implementation and config baselines; access review tickets |
| Secrets management | Secrets are managed outside source control with environment-based configuration. | `docs/SECRETS.md`; `docs/secrets-management.md`; secret rotation records |
| Incident response | Operational incidents are managed using defined runbooks and escalation paths. | `docs/runbooks/`; incident tracker; postmortems |
| Vulnerability management | Reports are triaged and remediated according to severity-based SLAs. | `docs/trust/coordinated-vulnerability-disclosure.md`; vuln tracker metrics; patch verification evidence |
| Third-party risk | Vendors are tiered, reviewed, and monitored through lifecycle governance. | `docs/trust/vendor-risk-policy.md`; subprocessor register; signed DPAs |
| Data rights | Customers retain ownership and can request export/deletion under documented process. | `docs/trust/customer-data-commitments.md`; request/fulfillment logs |
| Auditability | Key security-relevant events are captured and retained for investigation. | `shared/audit/`; retention policy records; audit log validation tests |

## How to Request Trust Information

- Security questionnaire and documentation requests: `security@valuefabric.example`
- Subprocessor and data handling inquiries: `privacy@valuefabric.example`
- Incident/security concerns: `security@valuefabric.example`

## Document Governance

- **Owner:** Security & Trust Program
- **Review cadence:** Quarterly, or sooner if major control/process changes occur
- **Last updated:** 2026-04-14
