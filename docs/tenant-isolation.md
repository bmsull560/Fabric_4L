# Tenant Isolation

## Model

- Every account-scoped object includes `tenantId`
- Backend uses tenant context middleware to extract `X-Tenant-ID`
- API handlers require tenant context via dependency injection
- Tests verify cross-tenant access is blocked

## Implementation

### Middleware

`TenantRequired` class extracts `X-Tenant-ID` from headers or query params and sets a context variable.

### Database

`MockTable` filters all `list()` and `get()` operations by tenant_id. Cross-tenant lookups return 404.

### Tests

`test_tenant_isolation.py` verifies:
- Same account accessible with correct tenant header
- Same account returns 404 with wrong tenant header
- Missing tenant header returns 400

## Production

Use PostgreSQL RLS (Row Level Security) policies:

```sql
CREATE POLICY tenant_isolation ON accounts
FOR ALL TO app_user
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

Set tenant context per request using `SET LOCAL app.current_tenant = '...'`.
