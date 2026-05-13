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

## Tenancy propagation contract

### Async workers (Celery tasks)
- `tenant_id` must be stored on the job record (e.g. `ScrapingJob.tenant_id`).
- Tasks read `tenant_id` from the job record, never from the task payload or request body.
- When calling downstream services, pass `tenant_id` in the `X-Tenant-ID` HTTP header.

### Service-to-service calls
- `tenant_id` is propagated via the `X-Tenant-ID` HTTP header.
- Receiving services extract `tenant_id` from authenticated request context, not from the request body.
- Missing or mismatched tenant context must fail closed (401/403).

### API routes
- `tenant_id` is extracted from authenticated request context (JWT claims, API key lookup, or trusted middleware).
- API routes must **never** accept `tenant_id` from the request body.
- Repository/service methods receive `tenant_id` as an explicit keyword argument.
