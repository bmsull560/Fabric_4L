# Vendor Risk Management Policy

## 1) Purpose

This policy defines the minimum controls for onboarding and monitoring third-party vendors
(including subprocessors, SaaS providers, infrastructure providers, and professional services)
that may process customer data or materially impact platform security, availability, or compliance.

## 2) Scope

Applies to all teams procuring, integrating, or renewing third-party services used by Value Fabric.

## 3) Vendor Risk Tiers

Classify vendors before onboarding:

- **Tier 1 (Critical):** Direct access to customer data, production credentials, or core systems.
- **Tier 2 (High):** Indirect influence on production security/availability or limited metadata access.
- **Tier 3 (Moderate/Low):** No production access and no customer data processing.

## 4) Minimum Due Diligence by Tier

| Control Area | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Security questionnaire | Required | Required | As needed |
| SOC 2 / ISO 27001 evidence | Required | Preferred | Optional |
| Pen test / vuln program evidence | Required | Preferred | Optional |
| DPA + confidentiality terms | Required | Required | As needed |
| Subprocessor transparency | Required | Required if applicable | Optional |
| Data residency / transfer review | Required | Required if applicable | Optional |
| BCDR evidence | Required | Preferred | Optional |

## 5) Required Pre-Onboarding Checks

1. Confirm business justification and data classification.
2. Complete legal review of contract terms (DPA, confidentiality, breach notice terms).
3. Complete security review (questionnaire + evidence validation).
4. Complete privacy review for personal data handling and cross-border transfer.
5. Document approval by control owner (Security), business owner, and procurement.

## 6) Ongoing Monitoring

- **Tier 1:** Review annually and at major contract changes.
- **Tier 2:** Review every 18 months.
- **Tier 3:** Review every 24 months or at renewal.
- Trigger ad hoc reassessment on security incidents, sanctions, material ownership change,
  or major control environment changes.

## 7) Findings and Exception Handling

- Findings must be categorized: Critical / High / Medium / Low.
- Critical and High findings require documented remediation plans with target dates.
- Exception approvals require Security + Legal sign-off and an expiration date.

## 8) Exit and Offboarding Requirements

On termination, vendor owners must verify:

- Access revocation (accounts, API keys, service principals).
- Data return or secure deletion with written attestation.
- Deactivation of integrations/webhooks.
- Update of the subprocessor register and asset inventory.

## 9) Evidence Artifacts

Maintain the following in the internal evidence repository:

- Completed questionnaires and assessment notes.
- Security/compliance reports and attestations.
- Approved exceptions and compensating controls.
- Annual monitoring records and offboarding attestations.
