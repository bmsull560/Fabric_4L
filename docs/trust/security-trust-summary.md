# Value Fabric Security & Trust Summary

This summary provides a customer-facing overview of our trust posture and where supporting
internal evidence is maintained.

## Core Commitments

- Protect customer data through layered security controls and least-privilege access.
- Operate documented incident response and vulnerability handling workflows.
- Govern third-party risk through structured due diligence and periodic reassessment.
- Provide transparency for data ownership, portability, and deletion commitments.

## Compliance Status

| Framework | Status | Last Audit | Next Audit | Evidence |
|---|---|---|---|---|
| SOC 2 Type II | In Progress | — | 2026-09-30 | `docs/compliance/control-matrix.md` |
| ISO 27001 | In Progress | — | 2026-12-31 | `docs/compliance/evidence-inventory-matrix.md` |
| GDPR | Active | 2026-04-14 | 2026-07-14 | `docs/compliance/control-matrix.md` |
| HIPAA | Conditional by tenant | — | Per tenant onboarding | `docs/compliance/hipaa-applicability-decision-record.md` |

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

## Penetration Testing

| Test | Date | Scope | Status | Report |
|---|---|---|---|---|
| OWASP ZAP Baseline | Weekly | L1-L6 APIs | Automated | `.github/workflows/release-evidence-bundle.yml` |
| External Penetration Test | 2026-03-15 | Full platform | Completed | Available under NDA — request via security@valuefabric.example |
| Container Security Scan | Per release | All L1-L6 images | Automated | Trivy SARIF in release evidence bundle |

## SBOM & Artifacts

- **SBOMs:** CycloneDX JSON per service, signed with Cosign, attached to every GitHub Release.
- **Download latest:** Visit the [Releases](https://github.com/bmsull560/Fabric_4L/releases) page and download `evidence-bundle.tar.gz`.
- **Vulnerability disclosure:** See `coordinated-vulnerability-disclosure.md` for scope and safe harbor.

## How to Request Trust Information

- Security questionnaire and documentation requests: `security@valuefabric.example`
- Subprocessor and data handling inquiries: `privacy@valuefabric.example`
- Incident/security concerns: `security@valuefabric.example`

## Document Governance

- **Owner:** Security & Trust Program
- **Review cadence:** Quarterly, or sooner if major control/process changes occur
- **Last updated:** 2026-05-06
