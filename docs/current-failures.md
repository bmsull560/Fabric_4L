# Current Failures Baseline

> Generated during Phase 2 baseline establishment.

## Summary

| Category | Pass | Fail | Error | Skip | Notes |
|----------|------|------|-------|------|-------|
| Frontend TypeScript | ✅ | 0 | 0 | - | `tsc --noEmit` passes |
| Frontend Build | ✅ | 0 | 0 | - | `pnpm run build` succeeds |
| Frontend Unit Tests | ~135 | 11 | 0 | - | 8 authClient + 3 EntityBrowser |
| Contract/Arch Tests | ~270 | 4 | 2 | ~25 | 2 import errors (jsonschema - fixed), 4 entity contract failures |
| Security Tests | - | - | 1 | - | 1 syntax error (XXE prevention) |
| Backend Layer Tests | TBD | TBD | TBD | - | Require `uv sync` per layer |

---

## Detailed Findings

### 1. Frontend Test Failures

#### `client/src/services/authClient.test.ts` — 8 failures
- **Root cause**: `global.fetch = vi.fn()` does not mock `window.fetch` in jsdom environment.
- **Error**: `fetch.mockResolvedValueOnce is not a function`
- **Fix**: Use `vi.stubGlobal('fetch', vi.fn())` instead of `global.fetch = vi.fn()`.

#### `client/src/pages/EntityBrowser.contract.test.tsx` — 3 failures
- **Root cause**: `getByText('Finance')` matches multiple elements (option + span).
- **Error**: `Found multiple elements with the text: Finance`
- **Fix**: Use `getAllByText` or more specific query.

### 2. Frontend Navigation Bug

#### `client/src/components/layout/Layout.tsx` — Broken settings link
- **Path**: `/settings/system/settings` does not exist in `shell/router.tsx`.
- **Router has**: `/settings` (redirects to `/settings/workspace`), `/settings/workspace`, `/settings/billing`, etc.
- **Fix**: Change nav link to `/settings`.

### 3. Backend Contract Test Failures

#### `tests/contract/test_entity_contract.py` — 4 failures
- **Root cause**: `EntitySummary` model has `confidence_label` and `status` as required fields (`Field(...)`), but tests expect them to be auto-derived from `confidence` via `@field_validator`. In Pydantic v2, `@field_validator` without `mode='before'` runs AFTER field validation, so missing required fields raise `ValidationError` before the validator can derive them.
- **Fix**: Add `mode='before'` to the validators, or change fields to optional with `Field(None, ...)`, or update tests to always provide the fields.

#### `tests/contract/test_graph_api_contract.py` & `test_layer3_contract.py` — Import errors
- **Root cause**: `jsonschema` module not installed in root Python environment.
- **Status**: ✅ Fixed by installing `jsonschema`.

### 4. Security Test Syntax Error

#### `tests/security/test_p1_20_xxe_prevention.py` — SyntaxError
- **Line 31**: Mismatched quotes: `assert '"lxml"' not in source, "Must NOT use lxml parser (XXE risk)'`
- **Fix**: Match opening and closing quotes.

### 5. pytest.ini Dependency Gap

- **Root cause**: `pytest.ini` addopts includes `--timeout=60`, `--randomly-seed=last`, `-n auto` but the plugins (`pytest-timeout`, `pytest-randomly`, `pytest-xdist`) are not in a root requirements file.
- **Impact**: Anyone running `pytest` from the root without these plugins gets `unrecognized arguments`.
- **Fix**: Either add the plugins to a root requirements/lock file, or make the addopts conditional.

---

## Remaining Investigations

- [ ] Run per-layer Python tests after `uv sync`
- [ ] Run frontend Playwright E2E tests
- [ ] Validate all health endpoints with live services
- [ ] Check OpenAPI spec completeness for all layers
- [ ] Run security test suite fully
- [ ] Run architecture tests fully
- [ ] Check for additional broken nav links or routes
