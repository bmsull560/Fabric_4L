# Governance

## Overview

Every AI-generated object must be reviewable, traceable, and approvable.

## Engineering Governance Linkage

These documents define the required engineering governance path for platform changes:

- [`docs/contract.md`](contract.md): canonical platform contract and enforcement targets
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md): contributor onboarding entry point
- [`governance/launch-drift-prevention-sop.md`](governance/launch-drift-prevention-sop.md):
  required approvals for contract, tenant-isolation, and compatibility-shim changes
- [`../.github/pull_request_template.md`](../.github/pull_request_template.md): PR confirmations
  required before review

Pull requests that touch backend, frontend, or API surfaces are expected to declare contract-shape,
tenant-isolation, and compatibility-shim impact explicitly and to link any required follow-up docs,
tests, or deprecation tracking.

## Review States

- `draft` - Initial generation
- `needs_review` - Flagged for human review
- `approved` - Validated by reviewer
- `modified` - Changed during review
- `rejected` - Discarded
- `published` - Approved and visible to stakeholders

## Review Queue

The Governance Review Queue surfaces:
- AI-generated hypotheses needing validation
- Formulas needing approval
- Evidence needing verification

## Production Gates

| Gate | Category | Status |
|------|----------|--------|
| Architecture | architecture | passed |
| Security | security | passed |
| Tenant Isolation | tenant_isolation | passed |
| Contract Drift | contract_drift | pending |
| Observability | observability | passed |
| Agent Safety | agent_safety | pending |

## Audit Log

Tracks:
- User actions
- Agent actions
- Review decisions
- Data changes

## Ground Truth

Validated truth objects store human-verified claims with evidence and reviewer attribution.
