# Contract Enforcement Audit — 2026-04-28

**Auditor:** `/contract-enforcement-auditor` workflow  
**Scope:** All 6 canonical contracts  
**Status:** 58% overall enforcement rate (estimated from contract.md assessment)

---

## Summary

| Contract | Documented | ESLint Rule | CI Blocking | Runtime Guard | Violations | Score |
|----------|------------|-------------|-------------|---------------|------------|-------|
| §2.1 Tenant Context Propagation | ✅ Yes | 🟡 Partial | ❌ No | 🟡 Partial | ~225 | ~60% |
| §2.2 DB Session Isolation | ✅ Yes | 🟡 Partial | ❌ No | 🟡 Partial | ~46 | ~40% |
| §2.3 Middleware/Auth Flow | ✅ Yes | 🟡 Warn | ❌ No | 🟡 Single middleware | ~42 | ~50% |
| §2.4 Tool Invocation Boundary | ✅ Yes | 🟡 Partial | ❌ No | ✅ ToolRegistry exists | ~19 | ~55% |
| §2.5 Agent Output Shape | ✅ Yes | 🟡 Warn | ❌ No | 🟡 OTel partial | ~13 | ~50% |
| §2.6 UI State Progression | ✅ Yes | ✅ Error | ❌ No | ❌ wouter used | ~80 | ~65% |

---

## §2.1 Tenant Context Propagation

**Status:** `proposed` → Target ratification: 2026-05-23

### Violations Found: ~225 instances

**Pattern: tenantId as function parameter**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer3-knowledge/src/migrations/migrate_tenant_ids.py` | multiple | 20 matches |
| `value-fabric/layer4-agents/tests/test_model_registry.py` | multiple | 13 matches |
| `value-fabric/shared/mcp_gateway/tests/unit/test_mcp_gateway_unit.py` | multiple | 11 matches |
| `value-fabric/layer3-knowledge/src/api/cache.py` | multiple | 7 matches |
| `value-fabric/layer3-knowledge/src/api/dependencies_tenant.py` | multiple | 4 matches |
| `value-fabric/layer2-extraction/src/layer2_extraction/api/routes/ontology.py` | multiple | 3 matches |

**Pattern: Direct header access for tenant ID**

| File | Line | Issue |
|------|------|-------|
| `value-fabric/layer4-agents/src/integration/layer2_client.py` | TBD | `req.headers` access |
| `value-fabric/layer4-agents/src/integration/layer3_client.py` | TBD | `req.headers` access |
| `value-fabric/layer4-agents/src/integration/layer5_client.py` | TBD | `req.headers` access |
| `value-fabric/shared/identity/middleware.py` | TBD | `req.headers` access |

### Enforcement Gaps

- [ ] **ESLint Rule:** `no-tenant-id-parameter` exists but is NOT enabled in production Python code
- [ ] **CI Gate:** No contract-specific CI gate; ruff linting only
- [ ] **Runtime Guard:** `GovernanceMiddleware` exists but coverage unknown

### Fix Suggestions

1. Enable runtime guard in `shared/identity/middleware.py` to detect tenantId parameters
2. Migrate 225 instances using `/deprecation-migrator AP-1`
3. Add CI gate for Python contract violations

---

## §2.2 DB Session Isolation Pattern

**Status:** `ratified` (2026-04-25) → Target enforcement: 2026-06-23

### Violations Found: ~46 instances

**Pattern: Explicit DB connect with tenant**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer2-extraction/src/db/*.py` | multiple | ~12 instances |
| `value-fabric/layer3-knowledge/src/db/*.py` | multiple | ~14 instances |
| `value-fabric/layer4-agents/src/db/*.py` | multiple | ~5 instances |

**Pattern: Raw SQL with tenant_id filtering**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer3-knowledge/src/retrieval/*.py` | multiple | ~8 instances |
| `value-fabric/layer5-ground-truth/src/eval/*.py` | multiple | ~4 instances |
| `scripts/analytics/*.py` | multiple | ~3 instances (whitelisted) |

### Enforcement Gaps

- [ ] **ESLint Rule:** Rules exist (`no-raw-tenant-query`, `no-explicit-db-connect`) but not enforced in Python
- [ ] **CI Gate:** `platform_contract_lint.py` mentioned but not found in CI
- [ ] **Runtime Guard:** RLS policies exist but SET LOCAL enforcement incomplete

### Fix Suggestions

1. Implement `get_db_from_context()` dependency in all FastAPI routes
2. Migrate raw SQL to ORM queries
3. Add contract validation to `make verify`

---

## §2.3 Middleware and Auth Flow

**Status:** `proposed` → Target ratification: 2026-05-23

### Violations Found: ~42 instances

**Pattern: Inline middleware definition**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer3-knowledge/src/api/routes/*.py` | multiple | ~28 instances |
| `value-fabric/layer4-agents/src/api/*.py` | multiple | ~14 instances |

### Enforcement Gaps

- [ ] **ESLint Rule:** `no-inline-middleware` is set to `"warn"` in frontend config (lines 46-47)
- [ ] **CI Gate:** No OpenAPI spec diff validation in CI
- [ ] **Runtime Guard:** Single middleware exists but not 8-phase pipeline

### Fix Suggestions

1. Change ESLint rule from `"warn"` → `"error"` in `frontend/.eslintrc.js`
2. Implement 8-phase middleware pipeline from `examples/canonical/middleware/pipeline.ts`
3. Create route manifest structure

---

## §2.4 Tool Invocation Boundary

**Status:** `proposed` → Target ratification: 2026-05-23

### Violations Found: ~46 instances

**Pattern: Inline tool definition in agent config**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer4-agents/src/agents/*.py` | multiple | ~15 instances |
| `value-fabric/layer4-agents/workflows/*.py` | multiple | ~4 instances |

**Pattern: Tools throwing exceptions**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer4-agents/src/tools/*.py` | multiple | ~18 instances |
| `value-fabric/layer4-agents/src/agents/*.py` | multiple | ~9 instances |

**Sample violation:** `value-fabric/layer4-agents/src/tools/knowledge.py:15-23`
```python
def _get_tenant_id() -> str:
    try:
        return str(require_context().tenant_id)
    except RuntimeError:
        return "default"  # Should return ToolResult with error status
```

### Enforcement Gaps

- [ ] **ESLint Rule:** `no-inline-tool-definition` is `"warn"`, `no-throw-in-tool` not enforced in Python
- [ ] **CI Gate:** No tool registry validation at build time
- [ ] **Runtime Guard:** ToolRegistry exists but coverage incomplete

### Fix Suggestions

1. Wrap all tool exceptions in `ToolResult` with `status: "error"`
2. Extract inline tools to `value-fabric/layer4-agents/src/tools/`
3. Register all tools with central ToolRegistry

---

## §2.5 Agent Output Shape and Traceability

**Status:** `proposed` → Target ratification: 2026-05-23

### Violations Found: ~13 instances

**Pattern: JSON.parse() on LLM responses**

| File | Line | Context |
|------|------|---------|
| `value-fabric/layer4-agents/src/agents/*.py` | multiple | ~10 instances |
| `value-fabric/layer4-agents/src/orchestrator.py` | multiple | ~3 instances |

### Enforcement Gaps

- [ ] **ESLint Rule:** `no-json-parse-agent-output` is `"warn"` (line 47 of .eslintrc.js)
- [ ] **CI Gate:** No OTel trace validation in CI
- [ ] **Runtime Guard:** OpenTelemetry spans partial

### Fix Suggestions

1. Switch to structured generation (Pydantic schema enforcement)
2. Remove all `json.loads()` on LLM responses
3. Add retry logic for validation failures

---

## §2.6 UI State Progression and Route Model

**Status:** `proposed` → Target ratification: 2026-05-23

### Violations Found: ~80 instances

**Pattern: Imperative navigation (router.push, history.push)**

| File | Line | Context |
|------|------|---------|
| `frontend/client/src/App.tsx` | multiple | 4 matches |
| `frontend/client/src/components/layout/Layout.tsx` | multiple | 3 matches |
| `frontend/client/src/components/workspace/IntelligenceShell.tsx` | multiple | 3 matches |
| `frontend/client/src/hooks/useAuth.ts` | multiple | 3 matches |
| `frontend/client/src/pages/*.tsx` | multiple | 38 instances |
| `frontend/client/src/components/*.tsx` | multiple | 18 instances |

**Pattern: URL string concatenation**

| File | Line | Context |
|------|------|---------|
| `frontend/client/src/api/client.test.ts` | TBD | 1 match |
| `frontend/client/src/components/layout/Layout.tsx` | TBD | 1 match |

### Enforcement Status

- [x] **ESLint Rule:** `no-imperative-navigation` and `no-url-concatenation` are `"error"` ✅
- [ ] **CI Gate:** No route manifest validation at build time
- [ ] **Runtime Guard:** Uses `wouter`, not state-machine-driven navigation

### Fix Suggestions

1. Replace `router.push("/path")` with `navigate("stateId", params)`
2. Implement state-machine route manifest from `examples/canonical/ui/route-manifest.ts`
3. Add CI validation for dead transitions

---

## CI Pipeline Analysis

### `continue-on-error: true` Found In:

| Workflow File | Line | Context | Risk |
|---------------|------|---------|------|
| `.github/workflows/pr-checks.yml:663` | Schemathesis L1 | Non-blocking | Medium |
| `.github/workflows/pr-checks.yml:670` | Schemathesis L2 | Non-blocking | Medium |
| `.github/workflows/pr-checks.yml:912` | Kustomize validation | Non-blocking | Low |
| `.github/workflows/test-reporting.yml:48` | Test artifact download | Non-blocking | Low |
| `.github/workflows/supply-chain.yml:65` | Grype SBOM scan | Non-blocking | High |
| `.github/workflows/pr-performance-gate.yml:132` | Baseline download | Non-blocking | Medium |
| `.github/workflows/ai-evals-pipeline.yml:418` | Eval results | Non-blocking | High |
| `.github/workflows/k8s-readiness.yml:247` | Kind cluster | Non-blocking | Low |

### Missing Contract Enforcement:

- ❌ No `contract-compliance.yml` workflow (referenced in contract.md but not found)
- ❌ No `platform_contract_lint.py` execution in CI
- ❌ ESLint errors don't fail CI (rules set to "warn")

---

## Contract Test Coverage

| Contract | Test File | Status |
|----------|-----------|--------|
| §2.1 Tenant Context | `tests/contract/test_tenant_architecture.py` | ✅ Exists |
| §2.2 DB Session | Partial in `tests/contract/test_l*.py` | 🟡 Partial |
| §2.3 Middleware | Not found | ❌ Missing |
| §2.4 Tool Boundary | `tests/contract/test_tool_manifests.py` | ✅ Exists |
| §2.5 Agent Output | Partial in `tests/contract/test_l4_*.py` | 🟡 Partial |
| §2.6 UI State | `tests/contract/test_l4_frontend_contract.py` | ✅ Exists |

---

## ESLint Plugin Status

**Location:** `eslint-plugin-fabric-contracts/`

### Rules Implemented (12/12): ✅ COMPLETE

| Rule | Contract | Status |
|------|----------|--------|
| `no-tenant-id-parameter` | §2.1 | ✅ Implemented |
| `no-req-tenant-access` | §2.1 | ✅ Implemented |
| `no-raw-tenant-query` | §2.2 | ✅ Implemented |
| `no-explicit-db-connect` | §2.2 | ✅ Implemented |
| `no-inline-middleware` | §2.3 | ✅ Implemented |
| `no-inline-tool-definition` | §2.4 | ✅ Implemented |
| `no-throw-in-tool` | §2.4 | ✅ Implemented |
| `no-json-parse-agent-output` | §2.5 | ✅ Implemented |
| `no-imperative-navigation` | §2.6 | ✅ Implemented |
| `no-url-concatenation` | §2.6 | ✅ Implemented |
| `no-private-imports` | General | ✅ Implemented |
| `no-circular-dependencies` | General | ✅ Implemented |

### Enforcement Gaps:

- 🟡 **Frontend config** (`frontend/.eslintrc.js`):
  - Lines 44-47: 5 rules set to `"warn"` instead of `"error"`
  - Rules affected: `no-raw-tenant-query`, `no-explicit-db-connect`, `no-inline-middleware`, `no-inline-tool-definition`, `no-json-parse-agent-output`
  
- ❌ **Python backend**: No ESLint equivalent for Python code (ruff doesn't have custom contract rules)

---

## Reference Implementation Status

**Location:** `examples/canonical/`

| Component | Status | Lines | Used in Production? |
|-----------|--------|-------|---------------------|
| `middleware/pipeline.ts` | ✅ Complete | ~520 | ❌ Not wired |
| `db/session-manager.ts` | ✅ Complete | ~450 | ❌ Not wired |
| `context/tenant-context.ts` | ✅ Complete | ~440 | ❌ Not wired |
| `tools/registry.ts` | ✅ Complete | ~380 | 🟡 Partially |
| `tools/example-tool.ts` | ✅ Complete | ~420 | ❌ Not wired |
| `agent/orchestrator.ts` | ✅ Complete | ~500 | ❌ Not wired |
| `ui/route-manifest.ts` | ✅ Complete | ~480 | ❌ Not wired |
| `ui/guards.ts` | ✅ Complete | ~380 | ❌ Not wired |
| `errors/error-shape.ts` | ✅ Complete | ~350 | 🟡 Partially |
| `errors/error-boundary.ts` | ✅ Complete | ~520 | 🟡 Partially |

**Total:** ~3,690 lines of reference code (per contract.md)

---

## Action Items

### Immediate (This Sprint)

1. **Fix ESLint enforcement:** Change 5 rules from `"warn"` → `"error"` in `frontend/.eslintrc.js`
2. **Add contract-compliance.yml:** Create CI workflow for contract validation
3. **Remove `continue-on-error`** from at least 2 high-risk CI steps

### Short-term (Next 4 weeks)

4. **Migrate tenantId parameters:** Target 225 instances in Python backend
5. **Fix tool exception handling:** Convert 27 `raise` statements to ToolResult
6. **Implement state-machine navigation:** Replace 80 imperative navigation calls

### Medium-term (Before 2026-06-23 enforcement)

7. **Wire reference implementations:** Connect canonical examples to production code
8. **Add Python contract linting:** Create ruff plugin or pre-commit hooks
9. **Complete middleware pipeline:** Migrate 42 inline middleware instances

---

## Deprecation Register Status

**Issue:** `scripts/ci/check_deprecations.py` expects `docs/deprecation_register.json` but file does not exist.

**Current tracking:** Uses `DEPRECATIONS.md` (markdown format)  
**Gap:** No machine-readable deprecation register for CI automation

**Recommendation:** Create `docs/deprecation_register.json` from `DEPRECATIONS.md` data.

---

## Appendix: Compliance Scores (from DEPRECATIONS.md)

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

*Report generated by Contract Enforcement Auditor workflow*  
*Next audit recommended: 2026-05-05 (weekly cadence)*
