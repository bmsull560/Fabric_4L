# Control Evidence Calendar

This document maps each SOC2/ISO control to its owner, evidence source, retention period, and next review date. It serves as the formal calendar for compliance attestation.

## Control Evidence Schedule

| Control ID | Control Domain | Owner GitHub Handle | Evidence Source Workflow | Retention | Last Review | Next Review |
|---|---|---|---|---|---|---|
| C-AC-01 | Access control + tenant auth integrity | @security-engineering | `.github/workflows/security-gates.yml` | 7 years | 2026-04-14 | 2026-05-14 |
| C-TI-01 | Tenant isolation and least privilege | @platform-engineering | `.github/workflows/contract-compliance.yml` | 7 years | 2026-04-14 | 2026-05-14 |
| C-AU-01 | Immutable audit trail | @security-engineering | `.github/workflows/audit-evidence.yml` | 7 years | 2026-04-14 | 2026-05-14 |
| C-DSAR-ACC | DSAR access fulfillment | @privacy-ops | Manual ticket records | 7 years | 2026-04-14 | 2026-07-14 |
| C-DSAR-DEL | DSAR deletion fulfillment | @privacy-ops | Manual ticket records | 7 years | 2026-04-14 | 2026-07-14 |
| C-DSAR-EXP | DSAR export portability | @product-engineering | Manual ticket records | 7 years | 2026-04-14 | 2026-07-14 |
| C-RET-01 | Retention and deletion enforcement | @data-governance | `.github/workflows/audit-evidence.yml` | 7 years | 2026-04-14 | 2026-07-14 |
| C-RES-01 | Data residency and transfer controls | @platform-engineering | `.github/workflows/environment-promotion.yml` | 7 years | 2026-04-14 | 2026-07-14 |
| C-SEC-03 | Secrets and third-party access governance | @security-engineering | `.github/workflows/secret-rotation.yml` | 7 years | 2026-04-14 | 2026-05-14 |
| P0-OIDC | Enterprise OIDC production gate | @identity-engineering | `.github/workflows/security-gates.yml` | 7 years | 2026-04-14 | 2026-07-14 |
| P0-MODEL | Model governance production gate | @ml-platform | Manual registry records | 7 years | 2026-04-14 | 2026-07-14 |
| P1-FLAGS | Feature flag operational governance | @platform-engineering | `.github/workflows/prod-readiness.yml` | 7 years | 2026-04-14 | 2026-05-14 |
| P1-QUOTA | Tenant quotas and rate limits | @platform-engineering | `.github/workflows/performance-load-tests.yml` | 7 years | 2026-04-14 | 2026-05-14 |
| P2-SOC2 | SOC2/ISO control package readiness | @compliance-engineering | `.github/workflows/release-evidence-bundle.yml` | 7 years | 2026-04-14 | 2026-07-14 |

## Stale Evidence Alert

A monthly scheduled workflow (`.github/workflows/compliance-evidence-review.yml`) opens a compliance review issue if any control evidence is stale (>30 days since last review).

## Review Procedures

1. **Monthly:** Controls with monthly cadence are reviewed by the owner via PR to update the "Last Review" date.
2. **Quarterly:** Full evidence completeness review against this matrix, producing a signed attestation artifact.
3. **Per PR:** Automation-backed controls publish machine-verifiable artifacts attached to the PR.

## Signed Attestations

Quarterly attestations are stored in `artifacts/audit/quarterly-attestation-YYYY-QN.json` and signed via GitHub attestations API with immutable Git commit linkage.
