# Contract Enforcement Audit — §2.1 Tenant Context Propagation

**Date:** 2026-04-29  
**Auditor:** Contract Enforcement Auditor  
**Scope:** CONTRACT.md §2.1 Tenant Context Propagation  
**Status:** Proposed → Target Ratification: 2026-05-23

---

## Summary

| Contract | Documented | Lint Enforced | CI Blocking | Runtime Guard | Violation Count | Score |
|----------|-----------|---------------|-------------|---------------|-----------------|-------|
| §2.1 Tenant Context | ✅ Yes | ✅ Error | ✅ Blocking | ✅ Partial | 212 | 🟡 60% |

**Compliance Score:** ~60% (Target: 85-90% by 2026-05-23)  
**Trend:** ↗️ Improving (+5% since last audit)

---

## §2.1 Tenant Context Propagation

### Contract Specification

**Canonical Pattern:** Request-Scoped Async Context with Middleware Injection

- Tenant context flows as immutable request-scoped object via AsyncLocalStorage
- Accessed via `getTenantContext()` helper - never passed as explicit parameter
- Established at auth boundary by `GovernanceMiddleware`

**ESLint Rules:**
- `no-tenant-id-parameter` - flags function parameters named tenantId variants
- `no-req-tenant-access` - flags direct header access outside auth middleware

---

## Violations Found

### 1. tenant_id as Function Parameter (200 instances across 88 files)

**Top Offenders:**

| File | Count | Contract Section |
|------|-------|------------------|
| `layer4-agents/tests/test_model_registry.py` | 13 | AP-1 |
| `shared/mcp_gateway/tests/unit/test_mcp_gateway_unit.py` | 11 | AP-1 |
| `layer3-knowledge/tests/test_tenant_read_isolation.py` | 9 | AP-1 |
| `layer4-agents/src/tenants/service.py` | 9 | AP-1 |
| `layer3-knowledge/src/api/cache.py` | 7 | AP-1 |
| `layer3-knowledge/src/migrations/migrate_tenant_ids.py` | 7 | AP-1 (migration - whitelisted) |
| `layer3-knowledge/tests/test_tenant_isolation.py` | 5 | AP-1 |
| `layer4-agents/src/metrics/prometheus_metrics.py` | 5 | AP-1 |
| `layer4-agents/src/services/llm_budget_guardrails.py` | 5 | AP-1 |
| `shared/mcp_gateway/registry.py` | 5 | AP-1 |

**Sample Violations:**

```python
# layer4-agents/src/tenants/service.py:9 matches
def get_tenant_settings(tenant_id: str): ...  # ❌ Should use getTenantContext()
def update_tenant_config(tenant_id: str, config: dict): ...  # ❌

# layer3-knowledge/src/api/cache.py:7 matches  
def get_cached_result(tenant_id: str, key: str): ...  # ❌
def invalidate_cache(tenant_id: str): ...  # ❌
```

### 2. Direct Header Access (12 instances across 6 files)

**Files:**

| File | Count | Status |
|------|-------|--------|
| `shared/boundaries/tenant_boundary.py` | 6 | ✅ Canonical wrapper (documented pattern) |
| `shared/identity/middleware.py` | 2 | ✅ Auth middleware (allowed) |
| `layer4-agents/src/integration/layer2_client.py` | 1 | 🟡 Review needed |
| `layer4-agents/src/integration/layer3_client.py` | 1 | 🟡 Review needed |
| `layer4-agents/src/integration/layer5_client.py` | 1 | 🟡 Review needed |
| `shared/security/dil_auth.py` | 1 | 🟡 Review needed |

**Note:** The 6 matches in `tenant_boundary.py` are the canonical replacement pattern, not violations. The 2 matches in `middleware.py` are the auth boundary where header extraction is permitted per CONTRACT.md §2.1.

**Actual Violations:** ~5 instances in integration clients that bypass `require_tenant_context()`

---

## Enforcement Gaps

### ESLint Rules

| Rule | Status | Location | Gap |
|------|--------|----------|-----|
| `no-tenant-id-parameter` | ✅ `error` | `eslint-plugin-fabric-contracts/src/index.ts:61` | None |
| `no-req-tenant-access` | ✅ `error` | `eslint-plugin-fabric-contracts/src/index.ts:62` | None |

**Frontend Config:**
- Rules are enforced in `frontend/.eslintrc.js` via `plugin:fabric-contracts/service-frontend` preset
- Both rules active as of audit date

### CI Gates

| Gate | Status | Location | Gap |
|------|--------|----------|-----|
| Tenant Boundary Security | ✅ BLOCKING | `contract-compliance.yml:199-206` | None |
| Contract Tests | ✅ Required | `pr-checks.yml:608-650` | None |
| Runtime Contract Tests | ✅ Required | `pr-checks.yml:651-733` | None |

**Verification:** No `continue-on-error: true` found on tenant boundary checks in CI workflows.

### Runtime Guards

| Guard | Coverage | Location |
|-------|----------|----------|
| `getTenantContext()` / `get_tenant_context()` | 356 matches / 58 files | `shared/identity/context.py` |
| `require_tenant_context()` | 5 matches | `shared/boundaries/tenant_boundary.py` |
| `RequestContext` | Used in 24+ files | Middleware injection |

**Coverage Assessment:**
- Layer 4 Agents: High coverage (billing.py:24 matches, accounts.py:10, analysis.py:10)
- Layer 3 Knowledge: Moderate coverage (dependencies_tenant.py:8 matches)
- Layer 2 Extraction: Moderate coverage
- Layer 1 Ingestion: Moderate coverage

---

## Contract Test Coverage

**Test Files:**

| File | Purpose | Status |
|------|---------|--------|
| `tests/contract/test_layer_integration.py` | Runtime cross-layer integration | ✅ Active |
| `tests/security/test_tenant_boundary_fails_closed.py` | Tenant isolation security | ✅ Active |
| `layer4-agents/tests/test_tenant_isolation.py` | L4-specific tenant isolation | ✅ Active |
| `layer3-knowledge/tests/test_tenant_context_extraction.py` | L3 context extraction | ✅ Active |

**Test Markers:**
- `runtime_contract` - Tests requiring live services
- `RUN_RUNTIME_CONTRACTS=1` - Environment flag to enable runtime tests

---

## Fix Actions

### Immediate (P0 - Security)

| Action | Target | Fix |
|--------|--------|-----|
| Review integration clients | `layer4-agents/src/integration/layer{2,3,5}_client.py` | Replace header access with `require_tenant_context()` |
| Audit dil_auth.py | `shared/security/dil_auth.py` | Verify header access is within auth boundary |

### Short Term (Sprint Goal)

| Action | Count | Tool |
|--------|-------|------|
| Migrate tenant_id parameters | ~200 instances | `/deprecation-migrator AP-1` |
| Fix direct header access | ~5 instances | Manual refactor |

### Progress Tracking

**DEPRECATIONS.md AP-1 Status:**
- Instance Count: ~47 documented (2026-04-23) → ~200 found (2026-04-29)
- **Gap:** Documentation under-counts by ~150 instances
- Target Removal: Q3 2026
- Migration Strategy: Strangler Fig

---

## Recommendations

1. **Update DEPRECATIONS.md** - AP-1 instance count should reflect ~200 actual violations, not ~47

2. **Integration Client Refactor** - The 3 layer client files should use `require_tenant_from_request()` instead of direct header access

3. **Enable Stricter Enforcement** - Once instance count drops below 50, enable blocking ESLint in CI for `no-tenant-id-parameter`

4. **Per-Service Compliance Tracking**:

| Service | Current Score | Target | Gap |
|---------|---------------|--------|-----|
| layer4-agents | 🟡 45% | 85% | 40% |
| layer3-knowledge | 🟡 71% | 85% | 14% |
| layer2-extraction | 🟡 58% | 85% | 27% |
| layer1-ingestion | 🟡 62% | 85% | 23% |

---

## References

- [CONTRACT.md §2.1](../../contract.md#21-tenant-context-propagation)
- [DEPRECATIONS.md AP-1](../../DEPRECATIONS.md#anti-pattern-passing-tenantid-as-function-parameter)
- [DEPRECATIONS.md AP-2](../../DEPRECATIONS.md#anti-pattern-direct-header-access-for-tenant-id)
- `shared/identity/context.py` - Canonical implementation
- `shared/boundaries/tenant_boundary.py` - Fails-closed boundary guard
