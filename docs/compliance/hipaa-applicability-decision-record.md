# HIPAA Applicability Decision Record

- **Decision ID:** HIPAA-ADR-2026-01
- **Decision date:** 2026-05-06
- **Decision owner:** Compliance Engineering (with Legal/Privacy)
- **Review cadence:** Quarterly and on any material data-scope change

## Decision Summary

HIPAA controls are **conditionally in scope** for Value Fabric deployments that process Protected Health Information (PHI) on behalf of a Covered Entity or Business Associate.

If a tenant ingests, stores, transmits, or derives PHI in Value Fabric, HIPAA safeguards and evidence requirements in this record become mandatory for that tenant environment.

## In-Scope Data Type Decision

PHI in scope includes (non-exhaustive):
- patient identifiers (name, MRN, member ID),
- treatment, diagnosis, claims, lab, and clinical note content,
- combinations of quasi-identifiers with health context,
- derived analytics that can re-identify an individual when linked.

Not in scope:
- fully de-identified data meeting HIPAA de-identification standard,
- synthetic test data with no production linkage.

## BAA Decision

Before enabling PHI processing, the following BAAs must exist and be recorded:
1. Customer <-> Value Fabric operator BAA.
2. Subprocessor BAAs for all PHI-touching vendors (cloud, logging, alerting, support tooling as applicable).
3. Tenant-specific exceptions documented with Legal approval.

## Required Safeguards for PHI Processing

### Administrative
- Assigned HIPAA security/privacy owners.
- Workforce access review at least quarterly.
- Incident response and breach notification workflow with HIPAA-specific timing checks.

### Technical
- Tenant-scoped RBAC and least-privilege enforcement.
- Immutable, queryable audit logs for PHI access actions.
- Encryption in transit and at rest.
- Access termination workflow integrated with identity lifecycle.

### Physical
- Inherited cloud provider physical controls validated via annual attestation package.

## Missing Controls Closure Requirement

If PHI is processed and any safeguard above is missing:
1. Create remediation issue with owner and due date.
2. Mark tenant HIPAA posture as "Conditional/At Risk".
3. Block production expansion for that tenant until closure evidence is attached.
4. Record exception approval only through Legal + Compliance dual sign-off.

## Evidence and Attestation Inputs

Required evidence sources:
- CI/CD compliance artifact bundle (`audit-evidence/*`).
- Quarterly access review records.
- Incident drill evidence with PHI scenario.
- Retention and deletion policy evidence.
