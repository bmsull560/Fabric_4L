# Quarterly Control Attestation Runbook

## Purpose

Define the repeatable quarterly process for attesting control design and operating effectiveness with auditable sign-off checkpoints.

## Scope

- Controls listed in `docs/compliance/evidence-inventory-matrix.md`.
- Governance readiness controls from P0/P1/P2 production-readiness documents.

## Roles

- **Control Owner:** validates control operation and evidence completeness.
- **Compliance Reviewer:** verifies evidence quality, retention, and approval traceability.
- **Security Reviewer:** validates security-sensitive controls.
- **Executive Signatory:** final quarterly attestation approval.

## Inputs

1. Current quarter evidence bundle from CI/CD artifacts.
2. Access review records for in-scope systems.
3. Incident and drill outputs.
4. Any control exceptions and remediation tickets.

## Procedure

1. **Evidence collection checkpoint**
   - Pull control artifacts generated in the quarter.
   - Confirm required metadata exists (`generated_at`, `control_id`, `owner`, `sanitized`).

2. **Control-by-control validation checkpoint**
   - For each control, verify:
     - evidence exists,
     - evidence is within frequency window,
     - retention path is defined,
     - approval history is present.

3. **Exception review checkpoint**
   - Validate unresolved exceptions have owner, risk rating, due date.
   - Confirm compensating controls are documented.

4. **Sign-off checkpoint**
   - Control owner signs each control row.
   - Compliance reviewer signs overall packet.
   - Security reviewer signs security/privacy controls.
   - Executive signatory approves quarter attestation statement.

5. **Archive checkpoint**
   - Store signed attestation package in compliance archive location.
   - Record immutable reference identifier in quarterly tracker.

## Output Template

- Quarter: `YYYY-Q#`
- Overall status: `PASS | PASS WITH EXCEPTIONS | FAIL`
- Controls reviewed: `<count>`
- Exceptions open: `<count>`
- Signatures:
  - Control Owner(s): `<name/date>`
  - Compliance Reviewer: `<name/date>`
  - Security Reviewer: `<name/date>`
  - Executive Signatory: `<name/date>`

## Escalation

If any critical control lacks evidence or approval trace:
- classify as attestation blocker,
- escalate to Compliance + Security leadership within 1 business day,
- track remediation before quarter close.
