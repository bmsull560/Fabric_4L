# Shared Tenant-Isolation Hostile Test Checklist

Use this checklist in every maintained layer service test package (`services/layer1-*` through `services/layer6-*`).

## Required hostile scenarios

- [ ] Tenant A cannot read Tenant B data.
- [ ] Tenant A cannot mutate Tenant B data.
- [ ] Missing tenant context fails closed (401/403 or explicit domain rejection).
- [ ] Repository/service methods receive tenant_id from trusted request context (not request body).

## Naming convention

- API/context propagation coverage: `test_api_tenant_propagation.py`
- Cross-tenant hostile coverage: `test_cross_tenant_hostile.py`

## Test implementation guidance

- Prefer request-context dependency overrides over request-body tenant injection.
- Assert repository method call kwargs include `tenant_id=<context tenant>`.
- Assert repository methods are not called when tenant context is absent.
- Include at least one read path and one mutate path per layer where applicable.
