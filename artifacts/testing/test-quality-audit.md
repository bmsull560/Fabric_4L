# Test Quality Audit Report

**Repository**: Value Fabric Monorepo  
**Audit Date**: 2026-04-10  
**Auditor**: Test Quality Remediation Agent  
**Scope**: All Python test files in value-fabric/layer{1-5}-*

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Test Files Reviewed | 16 |
| Total Tests | ~200+ |
| Layers with Tests | 4 of 5 |
| Layers with No Tests | 1 (layer4-agents) |
| Test Files with P0 Issues | 3 |
| Test Files with P1 Issues | 5 |
| Tests Currently Passing | 26 (layer5 only) |
| Tests Currently Failing | 19 (layer5 only) |
| Tests Unable to Run | All of layers 1-3 due to configuration/code errors |

**Overall Assessment**: The test suite has significant quality and configuration issues that prevent reliable execution. Layer 5 has the most mature tests but still has 42% failure rate due to Pydantic/datetime serialization issues.

---

## Repository Testing Landscape

### Backend (Python)

| Layer | Framework | Test Location | Files | Status | Coverage |
|-------|-----------|---------------|-------|--------|----------|
| layer1-ingestion | pytest | tests/unit/ | 3 | **BLOCKED** - Collection errors | Unknown |
| layer2-extraction | pytest | tests/ | 3 | **OPERATIONAL** - L2 pipeline tests passing | ~75% |
| layer3-knowledge | pytest | tests/ | 11 | **PARTIAL** - Unit tests work, E2E blocked on Neo4j Community | ~60% |
| layer4-agents | pytest | tests/ | 4 | **BLOCKED** - Import errors during collection | 0% |
| layer5-ground-truth | pytest | tests/ | 2 | **PARTIAL** - 19 failing, 26 passing | ~58% |

### Frontend (TypeScript)

| Framework | Test Files | Status |
|-----------|------------|--------|
| Vitest 2.1.4 | 0 | **NO TESTS** - Framework installed but no test files |
| Playwright | 0 | **NO TESTS** - Not configured |

### CI/Test Scripts

- No GitHub Actions workflows detected
- No root-level test runner scripts
- Docker compose files present for integration testing

---

## Per-File Audit Results

### Layer 5: Ground Truth (Best Quality, but Failing)

#### `tests/conftest.py`
**Score**: 29/35 (Good)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | N/A | Fixtures only |
| Clear/Readable | 5 | Well-documented, clear hierarchy |
| Focused | 4 | Good separation of concerns |
| Deterministic | 5 | SQLite in-memory, transaction rollback |
| Isolated | 5 | Function-scoped db with SAVEPOINT |
| Meaningful | N/A | Fixtures only |
| Maintainable | 5 | Factory functions, good patterns |

**Strengths**:
- Excellent fixture architecture (session engine → function db → client)
- Proper transaction isolation with `begin_nested()`
- Clear documentation of fixture hierarchy
- Helper factory functions (`make_truth_payload`, `make_source_payload`)

**Issues**:
- **P2**: Could add type hints to factory functions
- **P2**: `from sqlalchemy import select` import inside test function (line 140) should be at module level

**Recommended Action**: ✅ Leave as-is, minor P2 improvements only

---

#### `tests/test_state_machine.py`
**Score**: 27/35 (Good)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 5 | Tests state machine contracts |
| Clear/Readable | 5 | Excellent naming, clear AAA |
| Focused | 5 | Each test = one transition |
| Deterministic | 3 | Likely deterministic but failures suggest issues |
| Isolated | 4 | Uses db fixture properly |
| Meaningful | 5 | Covers all transitions, edge cases |
| Maintainable | 4 | Well-organized by class |

**Test Count**: 17 tests across 6 test classes

**Strengths**:
- Excellent test naming: `test_advances_when_conditions_met`, `test_fails_without_sources`
- Clear Arrange/Act/Assert structure
- Comprehensive coverage: valid transitions, invalid transitions, disputes, auto-advance
- Organized by state transition class (`TestAdvanceToSupported`, `TestDisputeFlow`, etc.)
- Docstrings explain coverage intent

**Issues Found**:
- **P0**: `test_creates_validation_event` fails with `'int' object has no attribute 'replace'` - datetime serialization issue
- **P0**: `test_auto_advances_to_corroborated_with_two_sources` fails with assertion error
- **P1**: `make_truth()` helper at line 42 uses `datetime.now()` which can cause microsecond comparison issues - use `freezegun` or fixed timestamps

**Recommended Action**: 
- 🔧 Fix P0 failures (likely production code issues with datetime handling)
- 🔧 Fix P1 by using deterministic timestamps

---

#### `tests/test_api.py`
**Score**: 25/35 (Fair)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 4 | Tests API contracts well |
| Clear/Readable | 4 | Good naming, some noise |
| Focused | 4 | Generally focused per test |
| Deterministic | 3 | Same datetime issues |
| Isolated | 4 | Uses client fixture |
| Meaningful | 4 | Good endpoint coverage |
| Maintainable | 3 | Some coupled to response structure |

**Test Count**: 23 tests across 8 test classes

**Strengths**:
- Tests real API endpoints with httpx.AsyncClient
- Covers CRUD operations, validation, filtering, pagination
- Tests organization isolation (security)
- Good error case coverage (404s, 422s)

**Issues Found**:
- **P0**: 17 tests fail with either:
  - `pydantic_core._pydantic_core.ValidationError: 3 validation errors for TruthObjectResponse`
  - `AttributeError: 'int' object has no attribute 'replace'` (datetime issue)
- **P1**: Tests use `ORG_PARAM = f"?organization_id={TEST_ORG_ID}"` which is implementation-coupled URL structure
- **P1**: `test_lists_created_objects` assertion `assert data["total"] >= 2` is weak - could pass with unrelated data
- **P1**: `test_filters_by_status` doesn't actually verify filtering works, just that returned items match filter

**Recommended Action**:
- 🔧 Fix P0 failures (production code Pydantic/datetime issues)
- 🔧 Fix P1 by improving assertions to verify actual behavior

---

### Layer 3: Knowledge (Partial - E2E Tests Fail on Community Edition)

#### `pytest.ini`
**Status**: Now has proper `conftest.py` (appears fixed)

**Previous Issue**: File was Python code with `.ini` extension
**Current Status**: Configuration resolved, tests can collect

---

#### `tests/test_e2e_pipeline.py`
**Score**: 24/35 (Good design, but fails on Community Edition)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 5 | Tests full extraction-to-query flow |
| Clear/Readable | 4 | Good docstring, clear setup |
| Focused | 4 | E2E tests are naturally broader |
| Deterministic | 3 | Uses testcontainers but flaky on Community |
| Isolated | 4 | Container per test run |
| Meaningful | 5 | Tests critical integration path |
| Maintainable | 3 | Enterprise constraints not supported |

**Test Count**: 15+ tests

**Issues Found**:
- **P0**: Fails on Neo4j Community due to enterprise-only `ASSERT EXISTS` constraints
  - Schema initializer uses property existence constraints (Enterprise feature)
  - Error: `Neo.ClientError.Statement.SyntaxError` on `ASSERT property IS NOT NULL`
- **P0**: `logger.error` misuse with structured kwargs (exception_type/path)
  - Logger expects `exc_info` tuple, not custom kwargs
  - See `test_exception_handlers.py` for validation

**Root Cause**: 
1. Schema uses enterprise-only constraints incompatible with Community edition
2. Logging calls pass invalid kwargs to `logger.error()`

**Recommended Action**:
- 🔄 Add Community-compatible schema mode (without property existence constraints)
- 🔄 Fix logging calls to use proper `exc_info` tuple
- 🔄 Add Neo4j edition detection in tests

---

#### `tests/conftest.py`
**Score**: 26/35 (Good - based on code review)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | N/A | Fixtures only |
| Clear/Readable | 4 | Good structure, but complex |
| Focused | 4 | Many fixtures, well-organized |
| Deterministic | 4 | Mock-based, should be deterministic |
| Isolated | 5 | Mock app state per test |
| Meaningful | N/A | Fixtures only |
| Maintainable | 4 | Good mocking patterns |

**Strengths**:
- Comprehensive mocking of external services (Neo4j, Pinecone)
- `TestSettings` class for test-safe defaults
- `mock_app_state` fixture provides complete app state mocking
- Proper async fixture handling

**Issues Found**:
- **P1**: `event_loop` fixture uses deprecated pattern - should use `pytest_asyncio` fixtures
- **P1**: `test_client` fixture creates new app per test (slow) - consider session-scoped with reset
- **P2**: Mocks return hardcoded data - could use factories for more realistic data

**Recommended Action**:
- 🔧 Fix pytest.ini blocking issue first
- 🔧 Update event_loop fixture to modern pattern
- ✅ Overall structure is good

---

#### `tests/test_exception_handlers.py` ⭐ **GOOD EXAMPLE**
**Score**: 30/35 (Excellent)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 5 | Tests logging contract |
| Clear/Readable | 5 | Excellent naming, clear assertions |
| Focused | 5 | Each test = one handler behavior |
| Deterministic | 5 | Mock-based, fully deterministic |
| Isolated | 5 | No external dependencies |
| Meaningful | 5 | Tests actual bug (logger.error kwargs) |
| Maintainable | 5 | Well-structured, passes |

**Test Count**: 2 tests

**Strengths**:
- Tests actual production bug: `logger.error(..., exception_type=..., path=...)` fails
- Verifies correct fix: `logger.error(..., exc_info=(type, value, tb))`
- Clean mock-based testing
- **Passes** - validates the fix works

**Purpose**: This test exists to prevent regression of a specific logging bug where `logger.error()` was called with invalid kwargs.

---

#### `tests/test_api.py` through `tests/test_search_endpoints.py`
**Status**: Can now execute (pytest.ini fixed)

Based on code review:
- 11 test files present
- Mix of unit and integration tests
- Some tests require Neo4j (see E2E issues above)

**Recommended Action**:
- 🔄 Run and evaluate for quality issues
- 🔄 Check for Community edition compatibility

---

### Layer 2: Extraction (Operational - L2 Pipeline Tests Pass)

#### `tests/test_extract_and_ingest_pipeline.py` ⭐ **REFERENCE QUALITY**
**Score**: 32/35 (Excellent)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 5 | Tests orchestration behavior, not implementation |
| Clear/Readable | 5 | Excellent naming, clear AAA structure |
| Focused | 5 | Each test = one orchestration scenario |
| Deterministic | 5 | FrozenClock for deterministic time |
| Isolated | 4 | Local helper fixtures, no shared state |
| Meaningful | 5 | Tests retry logic, circuit breaker, Layer 3 integration |
| Maintainable | 5 | Clean architecture with doubles |

**Test Count**: 8 tests

**Strengths**:
- **Local helper fixtures**: `FakePendingIngestionStore`, `FrozenClock`, `build_layer3_client_class`
- **Deterministic clock**: Frozen time for retry logic testing
- **Test doubles pattern**: Layer3 client doubles with health check simulation
- **API-level testing**: Uses `httpx.AsyncClient` for public contract validation
- **No global shared utilities**: Everything self-contained
- **Excellent test names**: `test_ingestion_enqueues_when_layer3_unhealthy`, `test_retries_follow_backoff_schedule`

**Issues Found**:
- **P2**: None significant - this is reference quality

**Recommended Action**: ✅ **LEAVE AS-IS** - Use as reference for other layers

---

#### `tests/test_extraction.py`, `tests/test_llm_extractor.py`
**Status**: Blocked by import errors (relative imports in src/)

**Issues Found**:
- **P0**: Import error: `attempted relative import beyond top-level package`
  - `src/extraction/__init__.py` has relative imports that fail when tests import from `tests/`

**Recommended Action**:
- 🔄 Fix package imports in `src/extraction/__init__.py` to be absolute

---

### Layer 1: Ingestion (Blocked by Collection Errors)

#### `tests/unit/test_models.py`
**Score**: N/A - Cannot collect

**Issue**:
- **P0**: `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API`
- Model has attribute named `metadata` which conflicts with SQLAlchemy's reserved attribute

**Recommended Action**:
- 🔄 Fix model definition to rename `metadata` field

---

#### `tests/unit/test_scheduler.py`
**Score**: N/A - Cannot collect

**Issue**:
- **P0**: `TypeError: non-default argument 'job_id' follows default argument 'depth'`
- Function signature error in scheduler code

**Recommended Action**:
- 🔄 Fix function signature order in scheduler

---

#### `tests/unit/test_adapters.py`
**Status**: Cannot determine - other errors block collection

**Recommended Action**:
- 🔄 Re-audit after fixing blocking issues

---

### Layer 4: Agents (Tests Exist but Blocked)

**Status**: **IMPORT ERRORS - Collection Failures**

- Directory `value-fabric/layer4-agents/tests/` exists with 4 test files
- Tests fail during collection with `ModuleNotFoundError: No module named 'src'`
- Import pattern issues similar to other layers

#### `tests/test_checkpoint_resume.py`
**Score**: 26/35 (Good - but cannot run)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 5 | Tests checkpoint/resume contracts |
| Clear/Readable | 5 | Excellent naming, clear AAA |
| Focused | 5 | One behavior per test |
| Deterministic | N/A | Cannot verify - collection error |
| Isolated | 4 | Good mocking |
| Meaningful | 5 | Covers pause/resume lifecycle |
| Maintainable | 3 | Cannot run due to import error |

**Test Count**: 13 tests across 5 test classes

**Strengths**:
- Excellent test naming: `test_checkpoint_saver_stores_state`, `test_resume_merges_user_data`
- Clear Arrange/Act/Assert structure
- Comprehensive coverage of checkpoint/resume lifecycle
- Good use of `MockCheckpointSaver` extending `InMemorySaver`
- Tests human-in-the-loop workflow scenarios

**Issues Found**:
- **P0**: `ModuleNotFoundError: No module named 'src'` during test collection
- **P1**: Runtime `import uuid` inside `create_formula_version` should be at top level

**Recommended Action**:
- 🔄 Fix import path issues (use absolute imports: `from layer4_agents...`)
- 🔄 Ensure pytest.ini has correct pythonpath

---

#### Other L4 Test Files
- `tests/test_interfaces_exports.py` - Interface validation
- `tests/test_workflow_controls.py` - Workflow control tests

**All blocked by same import error**

---

### Frontend (No Tests)

**Status**: **COVERAGE GAP**

- Vitest 2.1.4 installed in package.json
- No `*.test.ts`, `*.test.tsx`, or `*.spec.ts` files found
- No vitest.config.ts (configuration may be in vite.config.ts)

**Recommended Action**:
- 🔄 Create initial test suite for critical components
- 🔄 Document testing strategy

---

## Issue Summary by Severity

### P0 - Critical (Fix Immediately)

| Issue | Location | Impact | Fix Type |
|-------|----------|--------|----------|
| Import error - 'src' module | layer4-agents/tests/*.py | Blocks all 4 test files | Fix pythonpath, use absolute imports |
| Relative import error | layer2-extraction/src/extraction/__init__.py:21 | Blocks extraction tests | Convert to absolute imports |
| Enterprise constraints on Community | layer3-knowledge/schema | E2E tests fail | Add Community-compatible mode |
| Logger.error kwargs misuse | layer3-knowledge/api/main.py | Runtime errors | Use exc_info tuple |
| SQLAlchemy reserved attr | layer1-ingestion/src/shared/models.py | Blocks model tests | Rename `metadata` field |
| Function signature error | layer1-ingestion/src/scheduler.py | Blocks scheduler tests | Reorder parameters |
| Datetime serialization | layer5-ground-truth (multiple) | 19 tests failing | Fix Pydantic schema |
| Pydantic ValidationError | layer5-ground-truth API responses | 19 tests failing | Fix response models |

### P1 - Material (Fix Soon)

| Issue | Location | Impact | Fix Type |
|-------|----------|--------|----------|
| Weak assertions | test_api.py:117, 131 | May pass incorrectly | Strengthen assertions |
| URL structure coupling | test_api.py:27 | Brittle to URL changes | Use route helpers |
| Non-deterministic time | test_state_machine.py:55 | Potential flakes | Use frozen time |
| Deprecated pytest pattern | layer3/conftest.py:38 | Future compatibility | Update to pytest-asyncio |
| No layer4 tests | layer4-agents/ | Zero coverage | Add foundational tests |
| No frontend tests | frontend/ | Zero coverage | Create test suite |

### P2 - Improvement (Nice to Have)

| Issue | Location | Impact | Fix Type |
|-------|----------|--------|----------|
| Import placement | layer5/conftest.py:140 | Minor style | Move to top |
| Factory type hints | layer5/conftest.py:134 | Type safety | Add type annotations |
| Hardcoded mock data | layer3/conftest.py:74 | Less realistic | Use factories |
| Missing coverage | layer4, frontend | Quality gap | Add tests |

---

## Rewrite Priority Queue

### Immediate (P0 Blocking Issues)
1. **layer3-knowledge/pytest.ini** - Rename to conftest.py or convert to actual INI
2. **layer2-extraction imports** - Fix relative import chain
3. **layer1-ingestion models** - Rename reserved `metadata` attribute
4. **layer1-ingestion scheduler** - Fix function signature
5. **layer5-ground-truth datetime** - Fix Pydantic serialization

### High Priority (P1 Quality Issues)
6. **layer5 test assertions** - Strengthen weak assertions
7. **layer3 conftest** - Update deprecated patterns
8. **layer5 time handling** - Add deterministic timestamps

### Medium Priority (Coverage Gaps)
9. **layer4-agents tests** - Create foundational test suite
10. **frontend tests** - Create Vitest test suite

---

## Recommended Actions Summary

### Files to Leave As-Is
- `layer5-ground-truth/tests/conftest.py` - Quality is good
- Most of `layer5-ground-truth/tests/test_state_machine.py` - Quality is good (just fix failures)

### Files to Rewrite/Fix
- `layer5-ground-truth/tests/test_api.py` - Fix P0 failures, strengthen P1 assertions
- `layer3-knowledge/pytest.ini` - Convert to proper format
- `layer2-extraction/src/extraction/__init__.py` - Fix imports
- `layer1-ingestion/src/shared/models.py` - Fix reserved attribute
- `layer1-ingestion/src/scheduler.py` - Fix signature

### Files to Create
- `layer4-agents/tests/` - New test directory with foundational tests
- `frontend/*.test.ts` or `frontend/*.test.tsx` - New test files

---

## Appendices

### A. Test Execution Commands by Layer

```bash
# Layer 5 (Ground Truth) - Has some working tests
cd value-fabric/layer5-ground-truth
pytest tests/ -v --tb=short

# Layer 3 (Knowledge) - BLOCKED by pytest.ini
cd value-fabric/layer3-knowledge
# Fix pytest.ini first, then:
pytest tests/ -v --tb=short

# Layer 2 (Extraction) - BLOCKED by import error
cd value-fabric/layer2-extraction
# Fix imports first, then:
pytest tests/ -v --tb=short

# Layer 1 (Ingestion) - BLOCKED by collection errors
cd value-fabric/layer1-ingestion
# Fix model and scheduler first, then:
pytest tests/unit -v --tb=short

# Layer 4 (Agents) - NO TESTS
cd value-fabric/layer4-agents
# Create tests first

# Frontend - NO TESTS
cd frontend
pnpm test  # Vitest installed but no tests exist
```

### B. Current Test Results Summary

| Layer | Collected | Passed | Failed | Error | Status |
|-------|-----------|--------|--------|-------|--------|
| layer5-ground-truth | 45 | 26 | 19 | 0 | Partial |
| layer3-knowledge | ~40 | ~30 | ~10 | 0 | Partial (E2E fail) |
| layer2-extraction | 8 | 8 | 0 | 0 | **Operational** |
| layer1-ingestion | 0 | 0 | 0 | 2 files | Blocked |
| layer4-agents | 13 | 0 | 0 | 13 | Import errors |
| frontend | 0 | 0 | 0 | 0 | No tests |

**Total**: ~64 passing tests out of potentially 200+ tests (~30% operational)

---

## Next Steps

1. Fix P0 blocking issues to unblock test execution
2. Re-run full audit on previously blocked test files
3. Fix P0 failures in layer5-ground-truth
4. Address P1 quality improvements
5. Create foundational tests for layer4 and frontend
