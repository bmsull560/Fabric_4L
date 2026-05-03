# API Contract

## Base URL

```
/api/v1
```

## Authentication

All requests require `X-Tenant-ID` header. Optional `Authorization: Bearer <token>` for user-scoped actions.

## Endpoints

### Health
- `GET /health`
- `GET /metrics`

### Accounts
- `GET /v1/accounts`
- `POST /v1/accounts`
- `GET /v1/accounts/{account_id}`
- `PATCH /v1/accounts/{account_id}`
- `GET /v1/accounts/{account_id}/summary`

### Intelligence
- `GET /v1/accounts/{account_id}/signals`
- `POST /v1/accounts/{account_id}/signals/extract`
- `GET /v1/accounts/{account_id}/stakeholders`
- `GET /v1/accounts/{account_id}/ontology-match`
- `GET /v1/accounts/{account_id}/enrichment`

### Hypotheses
- `GET /v1/accounts/{account_id}/hypotheses`
- `POST /v1/accounts/{account_id}/hypotheses/generate`
- `PATCH /v1/hypotheses/{hypothesis_id}`

### Driver Tree
- `GET /v1/accounts/{account_id}/drivers`
- `GET /v1/accounts/{account_id}/value-tree`
- `POST /v1/accounts/{account_id}/drivers/generate`
- `PATCH /v1/drivers/{driver_id}`

### Evidence
- `GET /v1/accounts/{account_id}/evidence`
- `POST /v1/accounts/{account_id}/evidence/match`
- `GET /v1/evidence/{evidence_id}`

### Calculator
- `GET /v1/accounts/{account_id}/scenarios`
- `POST /v1/accounts/{account_id}/scenarios`
- `POST /v1/accounts/{account_id}/roi/calculate`
- `GET /v1/roi-calculations/{calculation_id}`

### Value Case
- `GET /v1/accounts/{account_id}/value-case`
- `POST /v1/accounts/{account_id}/value-case/generate`
- `PATCH /v1/value-cases/{value_case_id}`

### Context Engine
- `GET /v1/value-packs`
- `GET /v1/value-packs/{value_pack_id}`
- `GET /v1/formulas`
- `GET /v1/formulas/{formula_id}`
- `GET /v1/benchmarks`
- `GET /v1/ontology`

### Governance
- `GET /v1/governance/review-queue`
- `POST /v1/governance/review-decisions`
- `GET /v1/governance/prod-gates`
- `GET /v1/governance/audit-log`

### Agents
- `POST /v1/agents/runs`
- `GET /v1/agents/runs/{run_id}`
- `POST /v1/agents/runs/{run_id}/resume`
- `POST /v1/agents/runs/{run_id}/cancel`

## Error Format

```json
{
  "message": "string",
  "code": "string",
  "trace_id": "string"
}
```

## Review States

- `draft`
- `needs_review`
- `approved`
- `modified`
- `rejected`
- `published`
