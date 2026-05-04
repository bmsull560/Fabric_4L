# Production Invariants

**Generated:** April 29, 2026  
**Purpose:** Document non-negotiable security, isolation, and governance rules  
**Scope:** Cross-layer boundaries enforced by code

---

## Summary of Invariants

| Category | Count | Critical Files |
|----------|-------|----------------|
| Tenant Isolation | 8 rules | `shared/identity/middleware.py`, `shared/identity/dependencies.py` |
| Authentication | 6 rules | `shared/identity/dependencies.py`, `shared/identity/context.py` |
| Authorization | 5 rules | `shared/identity/dependencies.py` |
| Input Validation | 4 rules | Layer-specific validators |
| Rate Limiting | 3 rules | `shared/identity/middleware.py` |
| Audit Logging | 3 rules | `shared/identity/dependencies.py` |

---

## 1. Tenant Isolation Invariants

### 1.1 No Cross-Tenant Data Access

**Rule:** A tenant's data must never be accessible by another tenant, regardless of authentication status.

**Enforcement:**
- **Middleware validation:** `GovernanceMiddleware.dispatch()` checks `X-Tenant-ID` header against JWT claim
- **Query filtering:** All Neo4j queries include mandatory `tenant_id` predicate
- **RLS context:** `require_tenant_context` dependency ensures tenant_id presence

**Code Paths:**
```python
# shared/identity/middleware.py:312-323
header_tenant_id = request.headers.get("X-Tenant-ID")
if header_tenant_id:
    try:
        validate_context_consistency(context, header_tenant_id)
    except ValueError as e:
        logger.warning("Tenant ID mismatch: %s", e)
        return Response(
            content=f'{"error":"tenant_mismatch","detail":"{str(e)}"}',
            status_code=400,
        )
```

```python
# shared/identity/dependencies.py:66-82
async def require_tenant_context(context: RequestContext) -> RequestContext:
    if not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Include X-Tenant-ID header or valid tenant claim.",
        )
    return context
```

### 1.2 Tenant Context Required for RLS

**Rule:** Database queries without tenant context must fail.

**Enforcement:**
- **Dependency injection:** Routes using `Depends(require_tenant_context)` fail on missing tenant
- **Query helpers:** All Neo4j query helpers require `tenant_id` parameter

**Code Paths:**
```python
# value-fabric/layer3-knowledge/tests/test_tenant_read_isolation.py:45-51
async def test_requires_tenant_id(self, mock_session):
    with pytest.raises(ValueError, match="tenant_id is required"):
        await get_entity_by_id(mock_session, entity_id="abc", tenant_id="")
    
    with pytest.raises(ValueError, match="tenant_id is required"):
        await get_entity_by_id(mock_session, entity_id="abc", tenant_id=None)
```

### 1.3 Suspended/Pending/Deleted Tenant Access Denied

**Rule:** Tenants in non-active states cannot access resources.

**Enforcement:**
- **Status checks:** `GovernanceMiddleware._check_tenant_status()` enforces lifecycle states
- **Response codes:** 403 for suspended/pending, 404 for deleted (don't reveal existence)

**Code Paths:**
```python
# shared/identity/middleware.py:325-348
if tenant_status == "suspended":
    return Response(
        content='{"error":"tenant_suspended","detail":"Tenant is suspended."}',
        status_code=403,
    )
if tenant_status == "pending":
    return Response(
        content='{"error":"tenant_pending","detail":"Tenant is pending activation."}',
        status_code=403,
    )
if tenant_status == "deleted":
    return Response(
        content='{"error":"tenant_not_found","detail":"Tenant not found."}',
        status_code=404,  # Don't reveal existence
    )
```

### 1.4 Tenant ID Header Mismatch Detection

**Rule:** `X-Tenant-ID` header must match JWT tenant claim when present.

**Enforcement:**
- **Consistency validation:** `validate_context_consistency()` checks header against token
- **400 Bad Request:** Mismatches return 400, not 401/403 (client error, not auth failure)

**Code Paths:**
```python
# shared/identity/middleware.py:316-323
try:
    validate_context_consistency(context, header_tenant_id)
except ValueError as e:
    logger.warning("Tenant ID mismatch: %s", e)
    return Response(
        content=f'{"error":"tenant_mismatch","detail":"{str(e)}"}',
        status_code=400,
    )
```

### 1.5 Isolation Tier Validation

**Rule:** Only valid isolation tiers (shared, schema, database) are permitted.

**Enforcement:**
- **Context validation:** `RequestContext.is_isolation_tier_valid()` checks tier
- **Class-level constants:** `VALID_ISOLATION_TIERS` defines allowed values

**Code Paths:**
```python
# shared/identity/context.py:15-19, 94-96
ISOLATION_TIER_SHARED = "shared"
ISOLATION_TIER_SCHEMA = "schema"
ISOLATION_TIER_DATABASE = "database"
VALID_ISOLATION_TIERS = {ISOLATION_TIER_SHARED, ISOLATION_TIER_SCHEMA, ISOLATION_TIER_DATABASE}

def is_isolation_tier_valid(self) -> bool:
    return self.isolation_tier in self._valid_isolation_tiers
```

### 1.6 Cross-Tenant Query Logging

**Rule:** All cross-tenant queries by super-admins must be logged.

**Enforcement:**
- **Audit events:** `CROSS_TENANT_ACCESS` events emitted with `PrivilegedAccessDetails`
- **Session tracking:** `accessed_tenant_ids` set tracks cross-tenant access

**Code Paths:**
```python
# shared/identity/context.py:62-64
# Multi-Tenancy Hardening - Super-admin bypass tracking
accessed_tenant_ids: set[str] = field(default_factory=set)
privileged_session_start: float | None = None
```

```python
# shared/identity/dependencies.py:177-202
audit_details = PrivilegedAccessDetails(
    accessed_tenant_ids=list(context.accessed_tenant_ids),
    resource_types=["cross_tenant_query"],
    reason=reason,
)
await emit_audit_event(
    action=AuditAction.CROSS_TENANT_ACCESS,
    outcome=AuditOutcome.SUCCESS,
    actor_id=context.user_id,
    actor_type="super_admin",
)
```

---

## 2. Authentication Invariants

### 2.1 Valid Authentication Required

**Rule:** No unauthenticated access to protected resources.

**Enforcement:**
- **401 Unauthorized:** `require_authenticated` raises 401 without valid auth
- **Auth source validation:** `AUTH_SOURCE_UNKNOWN` is rejected

**Code Paths:**
```python
# shared/identity/dependencies.py:33-63
async def require_authenticated(context: RequestContext) -> RequestContext:
    if not context.tenant_id and not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if context.auth_source == AUTH_SOURCE_UNKNOWN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid authentication token required",
        )
    return context
```

### 2.2 JWT Configuration Validation (Production)

**Rule:** Production requires proper JWT configuration.

**Enforcement:**
- **Startup validation:** `validate_jwt_config()` runs at app startup
- **Required fields:** `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE`
- **Secret strength:** Minimum 32 characters

**Code Paths:**
```python
# shared/identity/dependencies.py:266-301
def validate_jwt_config() -> None:
    if environment == "production":
        if not jwt_secret:
            raise ValueError("JWT_SECRET is required in production.")
        if len(jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production.")
        if not jwt_issuer:
            raise ValueError("JWT_ISSUER is required in production.")
        if not jwt_audience:
            raise ValueError("JWT_AUDIENCE is required in production.")
```

### 2.3 Valid Auth Sources Only

**Rule:** Only JWT claims, API keys, and service accounts are valid auth sources.

**Enforcement:**
- **Context validation:** `RequestContext.is_auth_source_valid()` checks source
- **Unknown rejection:** `AUTH_SOURCE_UNKNOWN` contexts fail authentication

**Code Paths:**
```python
# shared/identity/context.py:21-25, 68-70, 98-100
AUTH_SOURCE_JWT = "jwt_claim"
AUTH_SOURCE_API_KEY = "api_key"
AUTH_SOURCE_SERVICE_ACCOUNT = "service_account"
AUTH_SOURCE_UNKNOWN = "unknown"
_valid_auth_sources = {
    AUTH_SOURCE_JWT, AUTH_SOURCE_API_KEY, AUTH_SOURCE_SERVICE_ACCOUNT, AUTH_SOURCE_UNKNOWN
}

def is_auth_source_valid(self) -> bool:
    return self.auth_source in self._valid_auth_sources
```

### 2.4 Unauthenticated Request Rejection

**Rule:** Requests without tenant context must be rejected at middleware.

**Enforcement:**
- **Middleware gate:** `GovernanceMiddleware` rejects unauthenticated requests
- **401 response:** Clear error message with `WWW-Authenticate` header

**Code Paths:**
```python
# shared/identity/middleware.py:298-310
if not context.tenant_id:
    logger.warning("Unauthenticated request rejected: path=%s", request.url.path)
    return Response(
        content='{"error":"authentication_required","detail":"A valid Bearer JWT or API key is required."}',
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )
```

---

## 3. Authorization Invariants

### 3.1 Tenant Admin Role Required

**Rule:** Admin operations require `tenant_admin` or `super_admin` role.

**Enforcement:**
- **403 Forbidden:** `require_tenant_admin` raises 403 for non-admins
- **Role check:** `RequestContext.is_tenant_admin()` validates roles

**Code Paths:**
```python
# shared/identity/dependencies.py:85-98
async def require_tenant_admin(context: RequestContext) -> RequestContext:
    if not context.is_tenant_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required",
        )
    return context
```

```python
# shared/identity/context.py:84-88
def is_tenant_admin(self) -> bool:
    if not self.roles:
        return False
    return "tenant_admin" in self.roles or "super_admin" in self.roles
```

### 3.2 Super Admin Role Required

**Rule:** Cross-tenant operations require `super_admin` role.

**Enforcement:**
- **403 Forbidden:** `require_super_admin` raises 403 for non-super-admins
- **Privileged access:** `require_privileged_access` factory adds audit requirements

**Code Paths:**
```python
# shared/identity/dependencies.py:101-114
async def require_super_admin(context: RequestContext) -> RequestContext:
    if not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return context
```

### 3.3 Permission-Based Access Control

**Rule:** Operations require specific permissions (e.g., `item:read`, `admin:write`).

**Enforcement:**
- **Permission factory:** `require_permission("permission:name")` creates dependencies
- **Any permission factory:** `require_any_permission()` for OR logic

**Code Paths:**
```python
# shared/identity/dependencies.py:212-233
def require_permission(permission: str):
    async def _check_permission(context: RequestContext) -> RequestContext:
        if not context.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return context
    return _check_permission
```

### 3.4 Privileged Access Requires Audit Reason

**Rule:** Super-admin cross-tenant access requires `X-Privileged-Reason` header.

**Enforcement:**
- **400 Bad Request:** Missing reason header returns 400
- **Audit logging:** All privileged access logged with `CROSS_TENANT_ACCESS` event

**Code Paths:**
```python
# shared/identity/dependencies.py:117-209
def require_privileged_access(privilege_reason_header: str = "X-Privileged-Reason"):
    async def _check_privileged(request: Request, context: RequestContext) -> RequestContext:
        if not context.is_super_admin():
            raise HTTPException(status_code=403, detail="Privileged access requires super admin role")
        
        reason = request.headers.get(privilege_reason_header)
        if not reason:
            raise HTTPException(
                status_code=400,
                detail=f"Privileged access requires {privilege_reason_header} header with audit reason",
            )
```

---

## 4. Rate Limiting Invariants

### 4.1 Per-Tenant Rate Limiting

**Rule:** Each tenant has independent rate limits.

**Enforcement:**
- **In-memory buckets:** `_tenant_rate_limit_buckets` maps tenant_id to (count, window_start)
- **Redis fallback:** Distributed rate limiting for multi-worker deployments

**Code Paths:**
```python
# shared/identity/middleware.py:50-54, 177-228
_tenant_rate_limit_buckets: dict[str, tuple[int, float]] = {}

def _check_tenant_rate_limit(tenant_id: str, requests_per_minute: int) -> tuple[bool, int]:
    with _buckets_lock:
        count, window_start = _tenant_rate_limit_buckets.get(tenant_id, (0, now))
        if now - window_start > RATE_LIMIT_WINDOW_SECONDS:
            count = 0
            window_start = now
        if count >= requests_per_minute:
            return False, retry_after
        _tenant_rate_limit_buckets[tenant_id] = (count + 1, window_start)
        return True, 0
```

### 4.2 Multi-Worker Safety Check

**Rule:** Multi-worker deployments require Redis for rate limiting.

**Enforcement:**
- **Runtime error:** `MultiWorkerRateLimitError` raised if Redis unavailable with >1 worker
- **Worker detection:** `_get_worker_count()` checks UVICORN_WORKERS, GUNICORN_WORKERS, WEB_CONCURRENCY

**Code Paths:**
```python
# shared/identity/middleware.py:231-239, 274-280
class MultiWorkerRateLimitError(RuntimeError):
    def __init__(self):
        super().__init__("Multi-worker deployment detected but REDIS_URL is not configured.")

if self.enable_per_tenant_rate_limiting and self._worker_count > 1:
    if not self._redis_client:
        raise MultiWorkerRateLimitError()
```

### 4.3 429 Response with Retry-After

**Rule:** Rate-limited requests receive 429 with `Retry-After` header.

**Enforcement:**
- **Standard response:** 429 Too Many Requests with `Retry-After` seconds

**Code Paths:**
```python
# shared/identity/middleware.py:366-370
return Response(
    content=f"Rate limit exceeded. Retry after {retry_after} seconds.",
    status_code=429,
    headers={"Retry-After": str(retry_after)},
)
```

---

## 5. Audit Logging Invariants

### 5.1 Privileged Access Audit Trail

**Rule:** All super-admin cross-tenant access must be audited.

**Enforcement:**
- **Audit event:** `CROSS_TENANT_ACCESS` with `PrivilegedAccessDetails`
- **Fields logged:** tenant_ids, resource_types, session_duration, reason, approval_ticket

**Code Paths:**
```python
# shared/identity/dependencies.py:177-204
audit_details = PrivilegedAccessDetails(
    accessed_tenant_ids=list(context.accessed_tenant_ids),
    resource_types=["cross_tenant_query"],
    session_duration_seconds=session_duration,
    reason=reason,
    approval_ticket=request.headers.get("X-Approval-Ticket"),
)
await emit_audit_event(
    action=AuditAction.CROSS_TENANT_ACCESS,
    outcome=AuditOutcome.SUCCESS,
    actor_id=context.user_id,
    actor_type="super_admin",
)
```

### 5.2 Failed Authentication Logging

**Rule:** Failed authentication attempts must be logged.

**Enforcement:**
- **Warning logs:** `logger.warning()` for rejected requests
- **Structured fields:** path, method, tenant_id, user_id

**Code Paths:**
```python
# shared/identity/middleware.py:300-304
logger.warning(
    "Unauthenticated request rejected: path=%s method=%s",
    request.url.path,
    request.method,
)
```

### 5.3 Tenant Status Change Logging

**Rule:** Access denied due to tenant status must be logged.

**Enforcement:**
- **Status-specific logs:** Suspended, pending, and deleted tenants logged separately

**Code Paths:**
```python
# shared/identity/middleware.py:329-347
logger.warning("Access denied for suspended tenant %s", context.tenant_id)
logger.warning("Access denied for pending tenant %s", context.tenant_id)
logger.warning("Access denied for deleted tenant %s", context.tenant_id)
```

---

## 6. Input Validation Invariants

### 6.1 UUID Format Validation

**Rule:** All ID fields must be valid UUID format.

**Enforcement:**
- **Pydantic models:** UUID fields use `UUID` type
- **Manual validation:** `UUID()` constructor validates format

### 6.2 Enum Value Validation

**Rule:** Enum fields must be within allowed values.

**Enforcement:**
- **Context validation:** `RequestContext.validate()` checks isolation_tier, auth_source
- **Set membership:** Values checked against `_valid_isolation_tiers`, `_valid_auth_sources`

**Code Paths:**
```python
# shared/identity/context.py:102-120
def validate(self) -> list[str]:
    errors = []
    if not self.is_isolation_tier_valid():
        errors.append(f"Invalid isolation_tier: {self.isolation_tier}")
    if not self.is_auth_source_valid():
        errors.append(f"Invalid auth_source: {self.auth_source}")
    if self.service_account_id and not self.service_account_scopes:
        errors.append("Service account must have scopes")
    return errors
```

### 6.3 Service Account Scope Consistency

**Rule:** Service accounts must have defined scopes.

**Enforcement:**
- **Validation error:** Missing scopes returns validation error
- **Scope checking:** `context.service_account_scopes` must be non-empty when `service_account_id` present

**Code Paths:**
```python
# shared/identity/context.py:117-118
if self.service_account_id and not self.service_account_scopes:
    errors.append("Service account must have scopes")
```

---

## Boundary Enforcement Points Summary

| Boundary | Enforcement Points | HTTP Status |
|----------|-------------------|-------------|
| Unauthenticated | `require_authenticated`, middleware | 401 |
| Invalid auth source | `require_authenticated` | 401 |
| Missing tenant | `require_tenant_context`, middleware | 400/401 |
| Tenant header mismatch | `validate_context_consistency` | 400 |
| Suspended tenant | `GovernanceMiddleware._check_tenant_status` | 403 |
| Pending tenant | `GovernanceMiddleware._check_tenant_status` | 403 |
| Deleted tenant | `GovernanceMiddleware._check_tenant_status` | 404 |
| Non-admin access | `require_tenant_admin` | 403 |
| Non-super-admin | `require_super_admin` | 403 |
| Missing permission | `require_permission` | 403 |
| Missing audit reason | `require_privileged_access` | 400 |
| Rate limit exceeded | `_check_rate_limit` | 429 |
| Invalid isolation tier | `RequestContext.validate()` | N/A (validation) |
| Invalid auth source | `RequestContext.validate()` | N/A (validation) |

---

## Test Coverage Requirements

Each invariant must have:
- **Positive test:** Proves intended behavior works
- **Negative test:** Proves forbidden behavior is blocked
- **Adversarial test:** Proves edge cases (spoofing, bypass attempts)

### Priority P0 (Block Release)
- Tenant isolation cross-read/write tests
- Auth bypass tests
- Tenant header mismatch tests
- Suspended/pending tenant access tests

### Priority P1 (Core Coverage)
- Rate limiting tests
- Permission-based authorization tests
- Privileged access audit tests
- JWT validation tests

### Priority P2 (Maintainability)
- Input validation edge cases
- Enum boundary tests
- Service account consistency tests
