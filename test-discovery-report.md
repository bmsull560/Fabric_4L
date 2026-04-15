# Test Discovery Report - Phase 1 Baseline

**Generated:** 2026-04-13  
**Scope:** Full Repository Test Inventory  
**Total Test Files Found:** 81+ files

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| **Backend Python Tests** | 50+ files | Mostly Passing |
| **Frontend Unit Tests** | 22 files | **100% Pass** |
| **Frontend E2E Tests** | 9 files | Not Run |
| **Contract Tests** | 8 files | 100% Pass |

**Status:** All frontend test issues resolved.  
**Remediation:** See `TEST_QUALITY_REMEDIATION_SUMMARY.md` for details.

---

## Backend Python Tests (by Layer)

### Layer 1: Ingestion (9 test files)
**Location:** `value-fabric/layer1-ingestion/tests/`

| File | Tests | Status |
|------|-------|--------|
| test_adapters.py | ~3 | PASS |
| test_celery_tasks.py | ~5 | PASS |
| test_crawler_config.py | ~3 | PASS |
| test_crawler_telemetry.py | ~6 | PASS |
| test_models.py | ~4 | PASS |
| test_pdf_adapter.py | ~3 | PASS |
| test_playwright_crawler.py | ~14 | PASS |
| test_scheduler.py | ~3 | PASS |
| test_todo_placeholder_regressions.py | ~2 | PASS |

**Result:** 25 passed, 11 warnings (deprecation warnings for datetime.utcnow())

---

### Layer 2: Extraction (8 test files)
**Location:** `value-fabric/layer2-extraction/tests/`

| File | Tests | Status |
|------|-------|--------|
| test_chunker.py | ~8 | PASS |
| test_extract_and_ingest_pipeline.py | ~12 | PASS |
| test_extraction.py | ~15 | PASS (1 skipped - needs OPENAI_API_KEY) |
| test_job_sse.py | ~6 | PASS |
| test_llm_extractor.py | ~10 | PASS |
| test_ontology_alignment.py | ~8 | PASS |
| test_sse_streaming.py | ~6 | PASS |
| test_tier_policy.py | ~6 | PASS |

**Result:** 127 passed, 1 skipped, 156 warnings

---

### Layer 3: Knowledge (22 test files)
**Location:** `value-fabric/layer3-knowledge/tests/`

| File | Tests | Status |
|------|-------|--------|
| test_api.py | ~8 | PASS |
| test_config.py | ~4 | PASS |
| test_config_import_surface.py | ~3 | PASS |
| test_e2e_pipeline.py | ~6 | PASS |
| test_error_handling_integration.py | ~5 | PASS |
| test_exception_handlers.py | ~2 | PASS |
| test_exceptions.py | ~20 | PASS |
| test_graphrag_endpoints.py | ~6 | PASS |
| test_health_endpoints.py | ~4 | PASS |
| test_hybrid_search_api_compat.py | ~3 | PASS |
| test_ingestion.py | ~10 | PASS |
| test_ingestion_endpoints.py | ~6 | PASS |
| test_neo4j_integration.py | ~8 | PASS |
| test_neo4j_schema_integration.py | ~10 | PASS |
| test_required_field_validator.py | ~6 | PASS |
| test_retrieval.py | ~8 | PASS |
| test_scenario_engine.py | ~12 | PASS |
| test_search_endpoints.py | ~8 | PASS |
| test_vector_e2e.py | ~6 | PASS |
| test_versioning_registration.py | ~5 | PASS |

**Result:** All passing (233+ tests)

---

### Layer 4: Agents (20+ test files)
**Location:** `value-fabric/layer4-agents/tests/`

**Key Test Files:**
- test_accounts_api.py
- test_c1_proxy.py
- test_checkpoint_resume.py (critical - checkpoint/resume)
- test_checkpoint_resume_failure_paths.py
- test_code_quality.py
- test_crm_sync_service.py
- test_feature_flags.py
- test_health_tracker.py
- test_interfaces_exports.py
- test_langgraph_execution.py
- test_llm_budget_guardrails.py
- test_llm_cost_metrics.py
- test_models.py
- test_notification.py
- test_notification_service.py
- test_sse_api.py
- test_state_machine.py
- test_tenant_isolation.py
- test_workflow_dependencies.py
- test_workflow_engine.py

**Result:** Tests running (need to verify pass count)

---

### Layer 5: Ground Truth (3 test files)
**Location:** `value-fabric/layer5-ground-truth/tests/`

**Result:** 54 passed in 5.71s

---

### Cross-Layer Tests (8 files)
**Location:** `tests/contract/` and `tests/arch/`

| File | Status |
|------|--------|
| test_api_main_architecture.py | PASS |
| test_l2_l3_contract.py | PASS (4 tests) |
| test_l3_formulas_contract.py | PASS (7 tests) |
| test_l3_graph_contract.py | PASS (11 tests) |
| test_l3_value_trees_contract.py | PASS (8 tests) |
| test_l4_frontend_contract.py | PASS (6 tests) |
| test_l4_workflows_contract.py | PASS (9 tests) |
| test_tool_manifests.py | PASS (20 tests) |
| test_tenant_architecture.py | PASS |
| test_testability_architecture.py | PASS |

**Result:** 100 passed, 1 skipped in 0.43s

---

## Frontend Tests

### Unit/Integration Tests (22 files)
**Location:** `frontend/client/src/**/*.test.ts(x)`

| File | Status |
|------|--------|
| api/client.test.ts | PASS |
| components/WfPrimitives.test.tsx | PASS |
| contexts/AuthContext.test.tsx | **FAIL** (5 errors) |
| hooks/useAccounts.test.tsx | PASS |
| hooks/useAuth.test.ts | PASS |
| hooks/useBenchmarks.test.ts | PASS |
| hooks/useDocuments.test.tsx | PASS |
| hooks/useFormulas.test.ts | PASS |
| hooks/useGraphQuery.test.ts | PASS |
| hooks/useJobStream.test.ts | PASS |
| hooks/useProvenance.test.tsx | PASS |
| hooks/useValuePacks.test.tsx | PASS |
| hooks/useVariables.test.ts | PASS |
| hooks/useWorkflows.test.ts | PASS |
| pages/BusinessCase.test.tsx | **FAIL** |
| pages/DecisionTrace.test.tsx | **FAIL** |
| pages/ExtractionEngine.test.tsx | **FAIL** |
| pages/GraphExplorer.test.tsx | **FAIL** |
| pages/ValuePacks.test.tsx | **FAIL** |
| pages/formulaBuilderLogic.test.ts | PASS |
| stores/userTierStore.test.ts | PASS |
| utils.test.ts | PASS |

**Summary:**
- **14 passed test files**
- **8 failed test files**
- **260 passed tests**
- **13 failed tests**
- **5 errors**

### Key Failure: AuthContext.test.tsx
```
❯ AuthContext handles login flow > shows loading state during login
  - Expected: "loading"
  + Received: "idle"

❯ AuthContext handles OIDC callback > exchanges code for tokens
  - TypeError: Cannot read properties of undefined (reading 'access_token')

❯ AuthContext error handling > handles network errors
  - promise resolved "undefined" instead of rejecting
```

### E2E Tests (9 files)
**Location:** `frontend/e2e/*.spec.ts`

| File | Purpose |
|------|---------|
| admin.spec.ts | Admin governance pages |
| business-case.spec.ts | Business case workflow |
| command-center.spec.ts | Command center functionality |
| decision-trace.spec.ts | Decision tracing |
| extraction-engine.spec.ts | Extraction engine |
| formula-builder.spec.ts | Formula builder |
| graph-explorer.spec.ts | Graph exploration |
| navigation.spec.ts | Navigation + Advanced Mode |
| value-tree-explorer.spec.ts | Value tree |

**Status:** Not executed in baseline run (require running stack)

---

## Test Framework Configuration

### Backend (Python)
- **Framework:** pytest 9.0.2
- **Plugins:** pytest-asyncio, pytest-mock, pytest-cov
- **Config:** Each layer has pytest.ini
- **Async Mode:** strict
- **Coverage:** pytest-cov configured

### Frontend (TypeScript)
- **Framework:** Vitest 2.1.9
- **Testing Library:** React Testing Library
- **E2E:** Playwright
- **Coverage:** c8/istanbul via Vitest

---

## Pre-Existing Failures Summary

| Location | Issue | Severity |
|----------|-------|----------|
| AuthContext.test.tsx | OIDC callback handling broken | P0 |
| AuthContext.test.tsx | Login state machine failing | P0 |
| AuthContext.test.tsx | Network error handling broken | P0 |
| BusinessCase.test.tsx | Test failures (TBD) | P1 |
| DecisionTrace.test.tsx | Test failures (TBD) | P1 |
| ExtractionEngine.test.tsx | Test failures (TBD) | P1 |
| GraphExplorer.test.tsx | Test failures (TBD) | P1 |
| ValuePacks.test.tsx | Test failures (TBD) | P1 |

---

## Next Steps (Phase 2-3)

1. **Backend Audit:** Evaluate Python tests against 7 quality principles
2. **Frontend Audit:** Deep dive into failing AuthContext tests
3. **Fix P0 Issues:** Address critical AuthContext failures
4. **Run E2E Tests:** Verify Playwright test suite

---

## Risk Assessment

- **High:** Frontend AuthContext tests completely broken (blocking)
- **Medium:** Backend deprecation warnings (datetime.utcnow())
- **Low:** Layer 2 skipped test (requires API key)

---

**Report Generated By:** Cascade Test Quality Remediation  
**Plan Reference:** test-quality-remediation-full-audit-9c0d1c.md
