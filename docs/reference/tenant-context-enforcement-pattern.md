# Tenant Context Enforcement Pattern

Use authenticated request context as the source-of-truth for tenant scope.

## Rules

- Never trust `tenant_id` values from request bodies for data access or writes.
- Keep body `tenant_id` only for compatibility contracts where clients still send it.
- When body `tenant_id` is present, reject mismatches against authenticated context with `403`.
- Emit structured audit log fields for mismatch events (`event_type`, route, operation, authenticated tenant, request tenant).

## Reference Implementation

- Shared helper: `services/api/app/core/tenant_enforcement.py`
- Route usage examples:
  - `services/api/app/routers/accounts.py`
  - `services/api/app/routers/intelligence.py`
  - `services/api/app/routers/evidence.py`
  - `services/api/app/routers/hypotheses.py`
  - `services/api/app/routers/drivers.py`
  - `services/api/app/routers/calculator.py`

## Layer 3 JWT Handling

Layer 3 model routes should consume shared identity dependencies instead of ad-hoc JWT parsing:

- `value_fabric/shared/identity/dependencies.py::require_tenant_context`
- Applied in `value_fabric/layer3/api/routes/models.py`
