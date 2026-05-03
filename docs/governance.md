# Governance

## Overview

Every AI-generated object must be reviewable, traceable, and approvable.

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
