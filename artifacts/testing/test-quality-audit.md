# Test Quality Audit Report

**Repository**: Value Fabric Monorepo  
**Audit Date**: 2026-04-09  
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
| layer2-extraction | pytest | tests/ | 1 | **BLOCKED** - Import error | Unknown |
| layer3-knowledge | pytest | tests/ | 10 | **BLOCKED** - pytest.ini misconfiguration | Unknown |
| layer4-agents | pytest | N/A | 0 | **NO TESTS** - Directory doesn't exist | 0% |
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

### Layer 3: Knowledge (Blocked by Configuration)

#### `pytest.ini`
**Score**: N/A - **CRITICAL CONFIGURATION ERROR**

**Issues Found**:
- **P0**: File contains Python code but has `.ini` extension - this is a conftest.py file misnamed!
- **P0**: pytest cannot parse it, blocking ALL layer 3 tests from running
- **P0**: Coverage options (`--cov=src`, `--cov-fail-under=80`) are set but tests can't run

**Recommended Action**:
- 🔄 **RENAME** to `conftest.py` OR convert to actual INI format
- 🔄 Remove Python code from INI file (move to proper conftest.py)

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

#### `tests/test_api.py` through `tests/test_search_endpoints.py`
**Status**: Cannot execute due to pytest.ini error

Based on code review of conftest.py and file structure:
- 10 test files present
- Mix of unit and integration tests
- Good fixture infrastructure (once unblocked)

**Recommended Action**:
- 🔄 Fix pytest.ini to enable test execution
- 🔄 Re-audit once tests can run

---

### Layer 2: Extraction (Blocked by Import Error)

#### `tests/test_extraction.py`
**Score**: 24/35 (Fair - based on partial code review)

| Principle | Score | Notes |
|-----------|-------|-------|
| Behavior-Focused | 4 | Tests model validation |
| Clear/Readable | 4 | Good naming |
| Focused | 3 | Some tests check multiple things |
| Deterministic | N/A | Cannot run |
| Isolated | N/A | Cannot run |
| Meaningful | 4 | Tests validation logic |
| Maintainable | 3 | Import errors suggest packaging issues |

**Test Count**: ~20+ tests based on file size (19KB)

**Issues Found**:
- **P0**: Import error: `attempted relative import beyond top-level package`
  - `src/extraction/__init__.py` has relative imports that fail when tests import from `tests/`
- **P1**: Tests use `from models.ontology import ...` which works due to `pythonpath = ["src"]` in pytest.ini but is fragile

**Root Cause**: Package structure issue. Tests run with `pythonpath = ["src"]` but src/extraction uses relative imports (`from ..models import`) which break the import chain.

**Recommended Action**:
- 🔄 Fix package imports in `src/extraction/__init__.py` to be absolute
- 🔄 Ensure consistent import style across layer

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

### Layer 4: Agents (No Tests)

**Status**: **CRITICAL GAP**

- Directory `value-fabric/layer4-agents/tests/` does not exist
- `pyproject.toml` has pytest configuration but no tests
- This is a significant coverage gap for a critical layer

**Recommended Action**:
- 🔄 Create tests directory
- 🔄 Add foundational tests for agent orchestration
- 🔄 Document as high-priority follow-up

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
| pytest.ini is Python code | layer3-knowledge/pytest.ini | Blocks all 10 test files | Rename to conftest.py |
| Relative import error | layer2-extraction/src/extraction/__init__.py:21 | Blocks all extraction tests | Convert to absolute imports |
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
| layer3-knowledge | 0 | 0 | 0 | 10 files | Blocked |
| layer2-extraction | 0 | 0 | 0 | 1 file | Blocked |
| layer1-ingestion | 0 | 0 | 0 | 2 files | Blocked |
| layer4-agents | N/A | N/A | N/A | N/A | No tests |
| frontend | 0 | 0 | 0 | 0 | No tests |

**Total**: 26 passing tests out of potentially 200+ tests (13% operational)

---

## Next Steps

1. Fix P0 blocking issues to unblock test execution
2. Re-run full audit on previously blocked test files
3. Fix P0 failures in layer5-ground-truth
4. Address P1 quality improvements
5. Create foundational tests for layer4 and frontend
