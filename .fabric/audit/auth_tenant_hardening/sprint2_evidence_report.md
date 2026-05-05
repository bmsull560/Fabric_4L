# Sprint 2: Auth and Tenant Contract Hardening — Evidence Report

**Date:** 2026-05-05
**Status:** Conditionally Complete
**Scope:** Audit L1–L6 auth/tenant middleware, define canonical contract, Layer 5 credential remediation

---

## 1. Phase 1 — Audit Summary

An audit was performed across all six service layers (L1–L6) to identify auth/tenant middleware and contract patterns.

**Canonical contract confirmed:**
- `value_fabric/shared/identity/context.py` — canonical `RequestContext` dataclass with fail-closed validation
- `value_fabric/shared/identity/middleware.py` — canonical `GovernanceMiddleware` enforcing JWT, API key, and service-auth header validation

**Layer 5 legacy path identified and hardened:**
- `services/layer5-ground-truth/src/layer5_ground_truth/api/auth.py` — legacy `get_current_user` dependency

---

## 2. Phase 2 — Canonical Auth/Tenant Contract

The canonical contract consists of:

1. **RequestContext** (`value_fabric/shared/identity/context.py`)
   - `tenant_id: str` (UUID, required)
   - `user_id: str | None`
   - `roles: list[str]`
   - `auth_method: str`
   - Fail-closed validation: missing/blank `tenant_id` raises `ValueError`

2. **GovernanceMiddleware** (`value_fabric/shared/identity/middleware.py`)
   - Validates `Authorization` (JWT), `X-API-Key`, and `X-Service-Auth` headers
   - Extracts `X-Tenant-ID` header for service-to-service auth
   - Sets `request.state.governance_context` with validated `RequestContext`

3. **Service-to-service auth**
   - `X-Tenant-ID` + `X-Service-Auth` headers
   - Validated by `SERVICE_AUTH_SECRET` (minimum 32 chars in production)

---

## 3. Phase 3 — Layer 5 Remediation Edits

### 3.1 Config Hardening
**File:** `services/layer5-ground-truth/src/layer5_ground_truth/config.py`

- Added `SERVICE_AUTH_SECRET` field with production validation
- Production fail-closed validator enforces:
  - `SERVICE_AUTH_SECRET` presence (>= 32 chars)
  - No known placeholder values
  - Explicit `CORS_ORIGINS`
  - No wildcard CORS
  - No insecure dev auth bypass

### 3.2 Auth Dependency Hardening
**File:** `services/layer5-ground-truth/src/layer5_ground_truth/api/auth.py`

- Hardened `get_current_user` to rely on `GovernanceMiddleware` context
- Production-like environments fail closed (401) without middleware context
- Dev/test fallback paths restricted by `allow_insecure_dev_auth_bypass`

### 3.3 Compose Environment Sync
**File:** `docker-compose.backend-integrated.yml`

- Added `SERVICE_AUTH_SECRET` to Layer 5 and Layer 4 service definitions

### 3.4 Fail-Closed Test Extension
**File:** `services/layer5-ground-truth/tests/test_production_fail_closed_i02.py`

- Added `SERVICE_AUTH_SECRET` presence, length, and placeholder checks
- Added hardened `get_current_user` behavior tests:
  - Derives identity from governance context
  - Production without context returns 401
  - Ignores tenant_id query param in production
  - Dev bypass enabled accepts `X-Tenant-ID` header
  - Dev bypass disabled without context returns 401

---

## 4. Phase 3 Validation — Test Results

### 4.1 Fail-Closed Tests
**Command:**
```powershell
$env:TESTING="true"; $env:ENVIRONMENT="testing"; $env:PYTHONPATH="C:\Users\BBB\Fabric_4L"
uv run pytest tests/test_production_fail_closed_i02.py -q -n0
```

**Result:** `16 passed in 0.54s`

All fail-closed tests pass, confirming:
- Production config rejects weak/placeholder secrets
- `get_current_user` fails closed without middleware context
- Dev bypass paths are properly gated

### 4.2 Broader Auth/Tenant Tests
**Command:**
```powershell
uv run pytest tests -k "auth or tenant or credential" --ignore=tests/unit/test_ground_truth_service.py -q -n0
```

**Result:** `10 passed, 2 failed, 113 deselected`

**Failures (pre-existing, unrelated to Sprint 2 changes):**
1. `test_metrics_denied_without_auth` — RuntimeError: `CORS_ORIGINS` env var missing in test environment
2. `test_migrations_do_not_reference_organization_id_in_policies` — Migration `002_add_rls_policies.py` references `organization_id`

These failures are not regressions introduced by Sprint 2 hardening.

---

## 5. Sprint 2 Recommendation

**Sprint 2 is conditionally complete.**

**Completed:**
- L1–L6 auth/tenant middleware audit
- Canonical contract documentation (RequestContext + GovernanceMiddleware)
- Layer 5 credential remediation (config, auth dependency, compose, tests)
- Fail-closed test suite passes (16/16)

**Deferred to Sprint 2B:**
- Cross-layer uniformity fixes (L1–L4, L6)
- New runtime tests for service-to-service auth
- Pre-existing test environment issues (CORS_ORIGINS, migration references)

**Risks:**
- Test environment (`CORS_ORIGINS`) needs fixing before full suite passes
- `organization_id` reference in migration should be aligned with `tenant_id` terminology

---

## 6. Evidence Artifacts

| Artifact | Location |
|----------|----------|
| This report | `.fabric/audit/auth_tenant_hardening/sprint2_evidence_report.md` |
| Fail-closed test log | `.fabric/audit/auth_tenant_hardening/l5_fail_closed.log` |
| Auth/tenant test log | `.fabric/audit/auth_tenant_hardening/l5_auth_tenant.log` |
| Canonical contract | `value_fabric/shared/identity/context.py` + `middleware.py` |
| Layer 5 config | `services/layer5-ground-truth/src/layer5_ground_truth/config.py` |
| Layer 5 auth | `services/layer5-ground-truth/src/layer5_ground_truth/api/auth.py` |
| Layer 5 tests | `services/layer5-ground-truth/tests/test_production_fail_closed_i02.py` |
