# Test Quality Remediation - Discovery Phase

**Date**: 2026-04-17  
**Status**: Phase 1 Complete - Phase 2 Audit In Progress

---

## Repository Structure

### Backend (Python)
- **Layers**: 6 layers (layer1-ingestion through layer6-benchmarks)
- **Framework**: pytest with pytest-cov
- **Test Files**: 71 test files across all layers
- **Coverage Target**: 80% (enforced in CI)

### Frontend (TypeScript/React)
- **Framework**: Vitest for unit/integration, Playwright for E2E
- **Test Files**: 28 test files (.test.ts, .test.tsx)
- **Total Tests**: 387 (379 passing, 8 failing)
- **Test Files Failed**: 8 of 28

---

## CI Integration

### GitHub Actions
- **File**: `.github/workflows/pr-checks.yml`
- **Coverage**: pytest-cov with --cov-fail-under=80
- **Linting**: ruff, mypy, bandit, pip-audit
- **Layers Tested**: Each layer independently (layer1-checks through layer5-checks)

### Frontend Test Commands
```bash
pnpm test          # Vitest unit tests
pnpm test:e2e      # Playwright E2E tests
```

---

## Test Frameworks

| Layer | Framework | Coverage Tool | Config |
|-------|-----------|---------------|--------|
| Frontend | Vitest | v8 (built-in) | vitest.config.ts |
| L1-L6 | pytest | pytest-cov | pyproject.toml |
| E2E | Playwright | n/a | playwright.config.ts |

---

## Failing Tests Analysis

### Pattern: Test Isolation Issues
The 8 failing tests all exhibit the same pattern:
- **Symptom**: `expected false to be true` (isSuccess never becomes true)
- **Behavior**: Tests pass when run in isolation, fail in full suite
- **Cause**: MSW mock handler pollution between tests

### Affected Test Files
1. `useBenchmarks.test.ts` - `fetches all benchmarks`
2. `useFormulaDependents.test.ts` - `fetches formulas that depend on this formula`
3. `useFormulas.test.ts` - `fetches all formulas`
4. `useFormulaVersions.test.ts` - `fetches version history for a formula`
5. `useHealthMonitor.test.ts` - `fetches system health successfully`
6. `usePlatformSettings.test.tsx` - `fetches tenant settings successfully`
7. `useVariables.test.ts` - `fetches all variables`
8. `useWorkflows.test.ts` - `fetches and normalizes active workflows`

### Root Cause
MSW server handlers are being overridden by previous tests and not properly reset. The `server.use()` calls in some tests are persisting across test boundaries.

---

## MSW Mock Structure

### Handler Organization
- `workflowMocks` - L4 workflow endpoints
- `jobStreamMocks` - L2 extraction job endpoints  
- `graphMocks` - L3 graph query endpoints
- `benchmarkMocks` - L3 benchmark endpoints
- `formulaMocks` - L3 formula endpoints
- `variableMocks` - L3 variable endpoints
- `provenanceMocks` - L3 provenance endpoints
- `businessCaseMocks` - L4 business case endpoints
- `valuePackMocks` - L3 value pack endpoints
- `valueTreeMocks` - L3 value tree endpoints
- `errorMocks` - Error simulation endpoints

### Issue Identified
Tests use `server.use()` to override handlers, but these overrides persist across tests instead of being reset. The `beforeEach` hook should reset MSW handlers to defaults.

---

## Coverage Gaps

### Frontend
- Some hooks lack error state tests
- E2E tests exist but not run in standard `pnpm test`

### Backend
- Layer 4 integration tests incomplete
- New integration service tests added (12 tests) ✓

---

## Next Steps (Phase 2: Audit)

1. Audit MSW reset patterns in test setup
2. Identify handler pollution sources
3. Fix test isolation issues
4. Add missing error state coverage

---

## Files for Audit

### Priority P0 (Failing)
- `frontend/client/src/hooks/useBenchmarks.test.ts`
- `frontend/client/src/hooks/useFormulaDependents.test.ts`
- `frontend/client/src/hooks/useFormulas.test.ts`
- `frontend/client/src/hooks/useFormulaVersions.test.ts`
- `frontend/client/src/hooks/useHealthMonitor.test.ts`
- `frontend/client/src/hooks/usePlatformSettings.test.tsx`
- `frontend/client/src/hooks/useVariables.test.ts`
- `frontend/client/src/hooks/useWorkflows.test.ts`

### Priority P1 (Improvement)
- `frontend/test/mocks/server.ts` - Add reset logic
- `frontend/test/setup.ts` - Verify MSW lifecycle
- `frontend/client/src/test-utils.tsx` - Check wrapper cleanup

### Priority P2 (Coverage)
- Add missing error state tests
- Add E2E coverage for critical paths
