# Fabric 4L Deprecation Map

**Status:** 🔄 IN PROGRESS  
**Last Updated:** 2026-04-28  
**Auto-Update Schedule:** Weekly (Mondays 00:00 UTC)

This document tracks all non-canonical patterns in the codebase and their migration paths to the canonical patterns defined in [CONTRACT.md](./contract.md).

---

## Migration Strategies

| Strategy | Description | Use When |
|----------|-------------|----------|
| **Strangler Fig** | Parallel operation, incremental shift | Most migrations; old/new patterns coexist |
| **Adapter** | Compatibility layer, old API delegates to new | Widely used interface that would require massive signature changes |
| **Big-Bang** | Coordinated sprint, all instances at once | Tight coupling across many files where incremental would be more complex |

---

## Deprecation Registry

### Anti-Pattern: Passing tenantId as Function Parameter

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | Functions accepting `tenantId`, `tenant_id`, `tenantID` as explicit parameters |
| **Canonical Replacement** | `getTenantContext()` from async scope (CONTRACT.md §2.1) |
| **Migration Strategy** | Strangler Fig |
| **Target Removal** | Q3 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~200 (as of 2026-04-29, corrected from ~47) |
| **Owning Team** | Platform Engineering |

**Locations:**
- `value-fabric/layer2-extraction/src/services/*.py` - 12 instances
- `value-fabric/layer3-knowledge/src/api/routes.py` - 18 instances
- `value-fabric/layer4-agents/src/tools/*.py` - 8 instances
- `frontend/client/src/hooks/*.ts` - 9 instances

**Migration Steps:**
1. Identify function accepting tenantId parameter
2. Replace parameter with `const ctx = getTenantContext()` call
3. Add null check and early return if context required
4. Update all call sites to remove tenantId argument
5. Remove parameter from function signature

---

### Anti-Pattern: Direct Header Access for Tenant ID

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | Code reading `req.headers['x-tenant-id']` or `req.tenant` outside auth middleware |
| **Canonical Replacement** | Auth middleware extracts once; downstream uses `getTenantContext()` (CONTRACT.md §2.1) |
| **Migration Strategy** | Big-Bang |
| **Target Removal** | Q2 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~18 (as of 2026-04-28) |
| **Owning Team** | Platform Engineering |

**Locations:**
- `value-fabric/layer1-ingestion/src/middleware/*.py` - 5 instances
- `value-fabric/layer3-knowledge/src/api/main.py` - 11 instances
- `value-fabric/layer4-agents/src/agents/*.py` - 7 instances

**Migration Steps:**
1. Consolidate all header reading into auth middleware
2. Replace direct access with `getTenantContext()` calls
3. Add runtime guard to detect new violations

---

### Anti-Pattern: Raw SQL with tenant_id Filtering

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | Raw SQL strings containing `tenant_id` filtering outside migrations/analytics |
| **Canonical Replacement** | ORM automatic scoping via `db.getSession()` (CONTRACT.md §2.2) |
| **Migration Strategy** | Strangler Fig |
| **Target Removal** | Q3 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~15 (as of 2026-04-23) |
| **Owning Team** | Data Engineering |

**Locations:**
- `value-fabric/layer3-knowledge/src/retrieval/*.py` - 8 instances
- `value-fabric/layer5-ground-truth/src/eval/*.py` - 4 instances
- `scripts/analytics/*.py` - 3 instances (whitelisted)

**Migration Steps:**
1. Identify raw SQL with tenant_id
2. Replace with ORM query builder
3. Ensure automatic tenant scoping applies
4. Add RLS safety net verification

---

### Anti-Pattern: Explicit DB Connect with Tenant

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | `db.connect(tenantId)` or `db.withTenant(tenantId)` calls |
| **Canonical Replacement** | `db.getSession()` which reads tenant from async scope (CONTRACT.md §2.2) |
| **Migration Strategy** | Adapter |
| **Target Removal** | Q2 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~28 (as of 2026-04-28) - L1 ingestion fixed |
| **Owning Team** | Platform Engineering |

**Locations:**
- `value-fabric/layer2-extraction/src/db/*.py` - 12 instances
- `value-fabric/layer3-knowledge/src/db/*.py` - 14 instances
- `value-fabric/layer4-agents/src/db/*.py` - 5 instances

**Migration Steps:**
1. Create adapter that delegates `db.connect(tenantId)` to `db.getSession()`
2. Update internal implementation to use context
3. Migrate call sites incrementally
4. Remove adapter once all sites migrated

---

### Anti-Pattern: Inline Middleware Definition

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | `app.use(middleware)` scattered across route files |
| **Canonical Replacement** | Route manifest with declared phase pipeline (CONTRACT.md §2.3) |
| **Migration Strategy** | Big-Bang |
| **Target Removal** | Q3 2026 |
| **Status** | ⏳ Not Started |
| **Instance Count** | ~42 (as of 2026-04-23) |
| **Owning Team** | API Team |

**Locations:**
- `value-fabric/layer3-knowledge/src/api/routes/*.py` - 28 instances
- `value-fabric/layer4-agents/src/api/*.py` - 14 instances

**Migration Steps:**
1. Define route manifest structure
2. Migrate one route at a time to declarative pipeline
3. Remove inline `app.use()` calls
4. Validate with middleware manifest validator

---

### Anti-Pattern: Inline Tool Definition in Agent Config

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | Tools defined as lambdas inside agent configuration objects |
| **Canonical Replacement** | Central ToolRegistry with schema-first definitions (CONTRACT.md §2.4) |
| **Migration Strategy** | Strangler Fig |
| **Target Removal** | Q3 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~19 (as of 2026-04-23) |
| **Owning Team** | Agent Team |

**Locations:**
- `value-fabric/layer4-agents/src/agents/*.py` - 15 instances
- `value-fabric/layer4-agents/workflows/*.py` - 4 instances

**Migration Steps:**
1. Extract tool implementation to standalone function
2. Define JSON Schema input contract
3. Register with ToolRegistry
4. Update agent to reference registered tool
5. Auto-generate framework bindings

---

### Anti-Pattern: Tools Throwing Exceptions

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | Tools using `throw` or `raise` instead of returning structured errors |
| **Canonical Replacement** | Return `ToolResult` with `status: "error"` (CONTRACT.md §2.4) |
| **Migration Strategy** | Strangler Fig |
| **Target Removal** | Q2 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~27 (as of 2026-04-23) |
| **Owning Team** | Agent Team |

**Locations:**
- `value-fabric/layer4-agents/src/tools/*.py` - 18 instances
- `value-fabric/layer4-agents/src/agents/*.py` - 9 instances

**Migration Steps:**
1. Wrap tool body in try/catch
2. Convert exceptions to `error()` result
3. Ensure `recoverable` flag is set correctly
4. Test agent's retry behavior

---

### Anti-Pattern: JSON.parse() on LLM Responses

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | `JSON.parse()` on agent/LLM response variables |
| **Canonical Replacement** | Structured generation with Pydantic validation (CONTRACT.md §2.5) |
| **Migration Strategy** | Strangler Fig |
| **Target Removal** | Q3 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~8 (as of 2026-04-28) - CRM webhooks and state manager fixed |
| **Owning Team** | Agent Team |

**Locations:**
- `value-fabric/layer4-agents/src/agents/*.py` - 10 instances
- `value-fabric/layer4-agents/src/orchestrator.py` - 3 instances

**Migration Steps:**
1. Define Pydantic output schema
2. Switch to structured generation (function calling)
3. Remove JSON.parse() calls
4. Add retry logic for validation failures

---

### Anti-Pattern: Imperative Navigation

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | `router.push()`, `history.push()`, direct URL manipulation |
| **Canonical Replacement** | `navigate()` from navigation service (CONTRACT.md §2.6) |
| **Migration Strategy** | Strangler Fig |
| **Target Removal** | Q3 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~56 (as of 2026-04-23) |
| **Owning Team** | Frontend Team |

**Locations:**
- `frontend/client/src/pages/*.tsx` - 38 instances
- `frontend/client/src/components/*.tsx` - 18 instances

**Migration Steps:**
1. Replace `router.push("/path")` with `navigate("stateId", params)`
2. Update route manifest with state definitions
3. Verify transition validity preserved

---

### Anti-Pattern: URL String Concatenation

| Field | Value |
|-------|-------|
| **Deprecated Pattern** | `"/tenant/" + tenantId + "/dashboard"` string concatenation |
| **Canonical Replacement** | `navigate()` with state IDs (CONTRACT.md §2.6) |
| **Migration Strategy** | Adapter + Strangler Fig |
| **Target Removal** | Q2 2026 |
| **Status** | 🔄 In Progress |
| **Instance Count** | ~34 (as of 2026-04-23) |
| **Owning Team** | Frontend Team |

**Locations:**
- `frontend/client/src/pages/*.tsx` - 22 instances
- `frontend/client/src/components/*.tsx` - 12 instances

**Migration Steps:**
1. Identify URL concatenation patterns
2. Replace with `navigate()` calls
3. Handle URL encoding automatically

---

## Resolved 2026-04-28 (Contract Enforcement Remediation)

**Phase 1: Critical Red Zones**

| Pattern | Fix Description | Files Modified |
|---------|-----------------|---------------|
| Direct Header Access | Removed `request.headers.get('X-Tenant-ID')` fallbacks in `get_tenant_id()` helpers | `layer2-extraction/src/api/routes/ontology.py`, `layer3-knowledge/src/api/dependencies_tenant.py` |
| DB Session Tenant Scoping | Added explicit `tenant_id` and `require_tenant` parameters to `get_db_session()` calls | `layer1-ingestion/src/crawler/decision_store.py`, `layer1-ingestion/src/compliance/robots_checker.py` |

**Phase 3: Data Integrity & Parsing (§2.5)**

| Pattern | Fix Description | Files Modified |
|---------|-----------------|---------------|
| json.loads on Webhooks | Replaced `json.loads()` with Pydantic `model_validate_json()` | `layer4-agents/src/api/routes/crm_webhooks.py` (Salesforce + HubSpot) |
| json.loads on Agent State | Replaced `json.loads()` with `TypeAdapter.validate_json()` | `layer4-agents/src/engine/state_manager.py` (load_state + get_history) |

**Phase 4: CI/CD Hardening**

| CI Gate | Change |
|---------|--------|
| Schemathesis L1 OpenAPI | Removed `continue-on-error: true` - now blocking |
| Schemathesis L2 OpenAPI | Removed `continue-on-error: true` - now blocking |
| Kustomize Validation | Removed `continue-on-error: true` - kubectl now required |
| Test Reporting Artifacts | Removed `continue-on-error: true` on artifact download |
| Performance Gate Baseline | Removed `continue-on-error: true` on baseline download |

## Completed Migrations

| Pattern | Removal Date | PR |
|---------|-------------|-----|
| layer2_client.py tenant_id parameter | 2026-04-29 | Removed tenant_id from extract_operational_signals() |
| llm_budget_guardrails.py tenant_id parameters | 2026-04-30 | Removed tenant_id from precheck_or_raise() and record_usage() |

---

## Weekly Report Command

```bash
# Generate current instance counts
make check-deprecations

# Or run directly
python scripts/ci/check_deprecations.py --format markdown
```

---

## Dashboard

**Contract Compliance Score:**

| Service | Score | Trend |
|---------|-------|-------|
| layer1-ingestion | 🟡 62% | ↗️ +5% |
| layer2-extraction | 🟡 58% | ↗️ +8% |
| layer3-knowledge | 🟡 71% | ↗️ +3% |
| layer4-agents | 🔴 45% | ↗️ +12% |
| layer5-ground-truth | 🟢 85% | → 0% |
| layer6-benchmarks | 🟢 90% | → 0% |
| frontend/client | 🟡 67% | ↗️ +7% |

---

## References

- [CONTRACT.md](./contract.md) - Canonical Platform Contract
- [/examples/canonical/](./examples/canonical/) - Reference Implementation
- [Architecture Decision Records](./docs/ADRs/) - Historical context
