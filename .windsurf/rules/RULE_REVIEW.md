# Rule Review: `.windsurf/rules/` vs. Actual Codebase

**Date:** 2026-04-28
**Scope:** `hard-constraints.yaml`, `dependency-rules.yaml`, `safety-rules.yaml`, `style-rules.yaml`
**Method:** Automated code search + manual validation across 4,188+ test files, 406 frontend tests, 34 CI workflows, and all layer source trees.

---

## Executive Summary

| Category | Count |
|----------|-------|
| ✅ Accurate & enforced | 10 |
| ⚠️ Path mismatch (fixable) | 6 |
| ❌ Wrong pattern (would false-positive) | 2 |
| 🆕 Missing rule (gap found) | 5 |
| 🔴 Actual violation in codebase | 2 |

**Bottom line:** The rules are architecturally sound but contain **path prefix errors** that prevent them from matching the actual directory structure, and **SR-003 references a non-existent decorator** that would cause widespread false positives. Two actual security violations were found in `crm_tools.py`.

---

## Critical Issues (Fix Immediately)

### 1. Path Prefix Error — Layers are under `services/`

**Impact:** 6 rules use `layer*/**/*.py` globs that will **never match** because layers live at `services/layer*/`.

**Affected rules:**
- `HC-003` — `layer4-agents/migrations/*.py` → `services/layer4-agents/migrations/*.py`
- `DR-002` — `layer*/**/*.py` → `services/layer*/**/*.py`
- `SR-001` — `layer*/**/*.py` → `services/layer*/**/*.py`
- `SR-003` — `layer*/src/api/**/*.py` → `services/layer*/src/api/**/*.py`
- `SR-006` — `layer*/src/api/**/*.py` → `services/layer*/src/api/**/*.py`

**Fix:** Prepend `services/` to all layer-related file globs.

---

### 2. SR-003: Wrong Auth Pattern

**Problem:** The rule looks for `@require_auth` decorator, but the codebase uses FastAPI dependency injection:

```python
from shared.identity.dependencies import require_authenticated
@router.get("/items")
async def get_items(context: RequestContext = Depends(require_authenticated)):
    ...
```

**Impact:** The rule would **false-positive flag every protected route** as missing auth.

**Fix:** Change trigger from `missing_decorator: @require_auth` to `missing_dependency: require_authenticated`.

---

### 3. style-rules.yaml: Wrong ESLint Config Path

**Problem:** Rule claims config is at `frontend/eslint.config.js` (flat config format). Actual file is `frontend/.eslintrc.js` (legacy format).

**Impact:** Agents looking for `eslint.config.js` will fail to find the config.

**Fix:** Update path to `frontend/.eslintrc.js`. Note: `@typescript-eslint/no-explicit-any` is `"off"` (allows gradual migration).

---

## Actual Violations Found in Codebase

### 4. SOQL Injection in CRM Tools (Missing Rule)

**File:** `services/layer4-agents/src/tools/crm_tools.py:132` and `:153`

```text
SOQL query construction interpolates prospect_id into AccountId and WhatId filters.
```

**Risk:** `prospect_id` is interpolated directly into SOQL strings. While URL-encoded for Salesforce REST API, the SOQL itself is concatenated.

**Fix needed:**
- Add new rule `SR-007: no-soql-string-interpolation`
- Fix the code to use parameterized SOQL or bind variables

---

### 5. Layer 4 Test Imports Layer 5

**File:** `services/layer4-agents/tests/test_tenant_lifecycle.py:392`

```python
from layer5_ground_truth.models.truth_object import (TruthObject, TruthSource, ...)
```

**Violation:** `DR-002` prohibits Layer 4 from importing Layer 5. This is a test file, so it may be intentional for integration testing, but it should be documented or moved to root `tests/`.

---

## Missing Rules (Gaps)

| ID | Topic | Rationale |
|----|-------|-----------|
| **SR-007** | No SOQL/SQL f-string injection | `crm_tools.py` violates this |
| **SR-008** | Dev auth bypass must not reach production | `DEV_AUTH_BYPASS=true` exists; must be production-gated |
| **DR-005** | Root `tests/` exempt from layer-order | Cross-layer integration tests legitimately import multiple layers |
| **ST-004** | No `any` type in TypeScript | `tsconfig.json` has `strict: true`, but `.eslintrc.js` allows `no-explicit-any: off` |
| **ST-005** | Tailwind v4 uses CSS config | No `tailwind.config.*` exists; config is in `index.css` |

---

## Verified & Correct Rules

These rules accurately reflect the codebase:

| Rule | Validation |
|------|------------|
| `HC-001` | CI contract tests enforce tool/skill sync |
| `HC-002` | `shared/identity/` is heavily guarded |
| `HC-004` | 80% coverage gates in `pr-checks.yml` |
| `HC-005` | gitleaks + Trivy secret scan in CI |
| `DR-001` | Zero frontend→backend imports found |
| `DR-003` | `shared/identity/` imports only `shared/` submodules |
| `DR-004` | Zero cross-pack imports found |
| `SR-005` | Vault/Infisical + ESO fully implemented |
| `SR-006` | `RedisRateLimiter` in all public-facing layers |
| `ST-001`–`ST-003` | Ruff, ESLint, mypy, tsc all run in CI |

---

## Recommendations

1. **Fix all path prefixes** in YAML rules and `registry/rules.json`
2. **Rewrite SR-003** to match `Depends(require_authenticated)` pattern
3. **Add SR-007** for SOQL/SQL string interpolation
4. **Add SR-008** for dev auth bypass production gating
5. **Fix `crm_tools.py`** SOQL injection (actual security bug)
6. **Document or move** L4→L5 test import in `test_tenant_lifecycle.py`
7. **Update style-rules.yaml** ESLint path and add Tailwind v4 note
8. **Re-run validation** after fixes using `scripts/ci/validate_rules.py` (when available)
