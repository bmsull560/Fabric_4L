# Spec: Fix 3 Remaining Production Readiness Issues

## Status
Ready for implementation

---

## Problem Statement

A code review identified three production readiness issues that must be resolved before the next release:

1. **`k8s/envs/prod/kustomization.yaml`** — Seven placeholder image digests (`sha256:1111...7777`) exist in a deployable manifest. These are non-pullable and would cause a production deployment failure. The file needs a template pattern so real digests are injected at deploy time, plus a CI guard to prevent placeholder values from reaching the cluster.

2. **`services/layer3-knowledge/src/config/manager.py`** — `_load_from_vault()` already raises `VaultSourceNotSupportedError` correctly (intentional v1 behavior; ESO is the recommended path). No code change needed, but a unit test and a release note are missing.

3. **`services/layer4-agents/src/database.py`** — The deprecated `get_tiered_db_session()` raises HTTP 501 for unsupported isolation tiers. 501 means "HTTP method not implemented" — wrong semantics. The canonical replacement `get_db_from_context()` already uses 422. `get_tiered_db_session()` needs 501→422 and a `DeprecationWarning`.

---

## Requirements

### R1 — kustomization.yaml placeholder digests

| ID | Requirement |
|---|---|
| R1.1 | Remove all `sha256:1111...7777` placeholder digests from `k8s/envs/prod/kustomization.yaml`. |
| R1.2 | Create `k8s/envs/prod/kustomization.yaml.template` with `digest: <resolved-by-ci>` markers. |
| R1.3 | The deployable `kustomization.yaml` must not contain any sequential placeholder digest. |
| R1.4 | Create `scripts/check-no-placeholder-digests.sh` that exits non-zero if any placeholder digest pattern is found. |
| R1.5 | Wire the check script into `.github/workflows/environment-promotion.yml` as a pre-deploy step. |
| R1.6 | `scripts/ci/prepare_kustomize_deploy.sh` (existing) remains the canonical resolver; the template and guard do not replace it. |

### R2 — Vault config manager unit test + release note

| ID | Requirement |
|---|---|
| R2.1 | Add a unit test asserting `_load_from_vault()` raises `VaultSourceNotSupportedError` when `type: vault` is configured. |
| R2.2 | Test must live in `services/layer3-knowledge/tests/` and pass with `pytest`. |
| R2.3 | Add a release note to `docs/governance/compatibility-debt-registry.md` documenting the intentional v1 behavior and the ESO migration path. |

### R3 — database.py deprecation + status code fix

| ID | Requirement |
|---|---|
| R3.1 | `get_tiered_db_session()` must emit `DeprecationWarning` on every call, directing callers to `get_db_from_context()`. |
| R3.2 | The `HTTPException` raised for unsupported isolation tiers must use `status_code=422`, not `501`. |
| R3.3 | Existing callers of `get_tiered_db_session()` in the codebase must be identified; if any exist outside tests, they must be migrated to `get_db_from_context()`. |
| R3.4 | Add or update a unit test asserting the 422 status code and the presence of the deprecation warning. |

---

## Acceptance Criteria

1. `k8s/envs/prod/kustomization.yaml` contains no `sha256:1111...7777` values.
2. `k8s/envs/prod/kustomization.yaml.template` exists with `<resolved-by-ci>` markers.
3. `scripts/check-no-placeholder-digests.sh` exits 1 when given a file with placeholder digests, exits 0 otherwise.
4. The check script is referenced in `.github/workflows/environment-promotion.yml`.
5. `pytest services/layer3-knowledge/tests/test_vault_config.py` passes.
6. `docs/governance/compatibility-debt-registry.md` contains a Vault v1 release note.
7. `get_tiered_db_session()` emits `DeprecationWarning` when called.
8. `get_tiered_db_session()` raises `HTTPException(status_code=422)` for unsupported tiers (not 501).
9. No production caller of `get_tiered_db_session()` remains outside of tests.
10. All new/modified tests pass under `pytest`.

---

## Implementation Approach

Steps are ordered by dependency; each step is independently verifiable.

1. **Strip placeholder digests from `kustomization.yaml`** — Remove the 7 `digest:` lines with placeholder values. Add a comment pointing to the template and the CI resolver script.

2. **Create `kustomization.yaml.template`** — Copy the current structure, replace each `digest:` value with `digest: <resolved-by-ci>`.

3. **Create `scripts/check-no-placeholder-digests.sh`** — Grep for the sequential placeholder pattern. Exit 1 with a clear message if found.

4. **Wire check into CI** — Add a step in `environment-promotion.yml` that runs the check script against `k8s/envs/prod/kustomization.yaml` before any `kubectl apply`.

5. **Add Vault unit test** — Create `services/layer3-knowledge/tests/test_vault_config.py` with a test that instantiates a config with `type: vault` and asserts `VaultSourceNotSupportedError` is raised.

6. **Add compatibility-debt-registry entry** — Document `VaultSourceNotSupportedError` as intentional v1 behavior, note ESO as the migration path, and link to the relevant config manager code.

7. **Fix `get_tiered_db_session()`** — Add `warnings.warn(...)` at function entry. Change `status_code=501` to `status_code=422` in the unsupported-tier branch. Verify no production callers remain.

---

## Files Touched

| File | Change |
|---|---|
| `k8s/envs/prod/kustomization.yaml` | Remove placeholder digests |
| `k8s/envs/prod/kustomization.yaml.template` | New — template with `<resolved-by-ci>` markers |
| `scripts/check-no-placeholder-digests.sh` | New — CI guard script |
| `.github/workflows/environment-promotion.yml` | Add pre-deploy check step |
| `services/layer3-knowledge/tests/test_vault_config.py` | New — unit test for `_load_from_vault()` |
| `docs/governance/compatibility-debt-registry.md` | Add Vault v1 release note |
| `services/layer4-agents/src/database.py` | Fix 501→422, add `DeprecationWarning` |
| `services/layer4-agents/tests/` | Add/update test for deprecation + 422 |

---

---

# Spec: Repo Cleanup Audit — Technical Debt Reduction Pass

## Status
Ready for implementation

---

## Problem Statement

A production-minded audit of the Fabric_4L repository identified concrete maintainability, safety, and DX issues across six categories. This spec covers the agreed scope: **quick wins** (low-risk, high-leverage) plus two higher-effort items explicitly requested — full WfPrimitives caller migration and CI security workflow consolidation.

The audit was constrained by the churn guard: no broad renames, no style-only diffs, no new dependencies, no touching unrelated files.

---

## Repo Cleanup Audit

### Category 1 — Dead / Orphaned Root-Level Scripts

**Issue:** Three root-level Python scripts are one-time migration artifacts with no ongoing purpose.
- `cleanup_pytest_cache.py` — hardcoded Windows path `c:/Users/BBB/Fabric_4L`; does nothing on Linux CI.
- `fix_all_relative_imports.py` — bulk-fixed Layer 3 relative imports; migration complete, no remaining `from ...X` patterns in `services/layer3-knowledge/src/`.
- `fix_test_imports.py` — bulk-fixed legacy `from shared.X` imports; migration complete, zero remaining `from shared.` in `services/` or `tests/`.

**Why it matters:** Orphaned scripts at the repo root create confusion about what's canonical tooling vs. one-off fixers. The Windows-path script silently does nothing in CI.
**Severity:** Low
**Recommended fix:** Delete all three files.
**Estimated effort:** Small

---

**Issue:** `compose-resolved.yml` (784 lines, generated Docker Compose artifact) is committed to the repo but not in `.gitignore`.
**Why it matters:** Generated artifacts in version control create merge conflicts and mislead readers about the canonical compose definition.
**Severity:** Low
**Recommended fix:** Add `compose-resolved.yml` to `.gitignore`.
**Estimated effort:** Small

---

**Issue:** `pyrightconfig.json` `strict` array references three files that no longer exist (`value_fabric/layer3/security/query_validator.py`, `value_fabric/layer3/security/monitor.py`, `value_fabric/layer3/analytics/manager.py`). The `value_fabric/` directory is deprecated and these paths resolve to nothing.
**Why it matters:** Pyright silently ignores missing strict paths, so the strict-mode enforcement is a no-op for those three entries. Misleads engineers into thinking those modules are type-checked strictly.
**Severity:** Low
**Recommended fix:** Remove the three dead paths from `pyrightconfig.json` `strict` array. Keep `tests/layer3/test_typed_payloads.py` (exists).
**Estimated effort:** Small

---

**Issue:** Three root-level spec files (`spec-oidc-audit.md`, `spec-test-report.md`) are committed alongside canonical docs. They are working documents, not reference documentation.
**Why it matters:** Root-level clutter; readers can't distinguish canonical docs from working notes.
**Severity:** Low
**Recommended fix:** Move to `specs/` directory (which already exists and contains similar working documents).
**Estimated effort:** Small

---

### Category 2 — Stale Contracts

**Issue:** All three `review_by` dates in `contracts/drift-allowlist.yaml` are `2026-05-15`, which is now past (today: 2026-05-18).
**Why it matters:** Stale allowlist entries mean known contract drift is no longer being actively reviewed. The drift check script reads this file; stale entries silently suppress failures.
**Severity:** Medium
**Recommended fix:** Update all three `review_by` dates to a future date (e.g., `2026-08-15`) and add a comment documenting the review outcome.
**Estimated effort:** Small

---

### Category 3 — Frontend: WfPrimitives Shim Migration

**Issue:** 81 production files import from `@/components/WfPrimitives`, a deprecated compatibility shim explicitly frozen against new additions. The shim re-exports from canonical Fabric/shadcn primitives. Callers import: `Btn`, `SectionCard`, `MetricCard`, `StatusBadge`, `DataTable`, `PageHeader`, `EntityBadge`, `EntityType`.

**Why it matters:** The shim is a maintenance liability — any change to the underlying primitives must be verified against the shim's re-export surface. New engineers don't know which import path is canonical. The shim's own JSDoc says "migrate callers to direct imports."
**Severity:** Medium
**Recommended fix:** Replace all `WfPrimitives` imports with direct imports from canonical locations:

| WfPrimitives export | Canonical import |
|---|---|
| `Btn` | `@/components/ui/button` → `Button` (aliased as `Btn` where needed, or rename) |
| `SectionCard` | `@/components/ui/fabric/FabricCard` |
| `MetricCard` | `@/components/blocks` |
| `StatusBadge` | `@/components/blocks` |
| `DataTable` | `@/components/ui/fabric` |
| `PageHeader` | `@/components/ui/fabric/PageHeader` |
| `EntityBadge` | `@/components/ui/fabric` |
| `EntityType` | `@/components/ui/fabric` (type import) |

After migration, delete `WfPrimitives.tsx` and remove its export from `components/index.ts`.
**Estimated effort:** Medium

---

### Category 4 — Frontend: Noise / Minor Issues

**Issue:** 10 files contain `"use client"` directives. This is a Next.js RSC directive — it is a no-op in Vite/React but creates confusion about the framework.
**Why it matters:** Engineers unfamiliar with the codebase may assume Next.js patterns apply. The directive is harmless but misleading.
**Severity:** Low
**Recommended fix:** Remove `"use client"` from all files in `apps/web/src/`. The shadcn/ui files (`form.tsx`, `sheet.tsx`, `toggle-group.tsx`, `command.tsx`, `sidebar.tsx`) were likely copied from a Next.js template — strip the directive.
**Estimated effort:** Small

---

**Issue:** `components/layout/Layout.tsx` (783 lines) is exported from `components/index.ts` but is not imported anywhere in the application. The router uses `GlobalLayout` exclusively.
**Why it matters:** Dead code at 783 lines is significant noise. It also contains a duplicate `vp-theme` localStorage write that conflicts with `ThemeContext`.
**Severity:** Low
**Recommended fix:** Verify no external consumers, then delete `Layout.tsx` and remove its export from `components/index.ts`.
**Estimated effort:** Small

---

### Category 5 — CI: Security Workflow Consolidation

**Issue:** Three overlapping security CI workflows run on PRs to `main`:
- `security-gate.yml` (77 lines) — runs `pytest tests/security/` on every PR
- `security-gates.yml` (653 lines) — comprehensive: Bandit, Semgrep, CodeQL, secret scanning, OWASP, tenant isolation
- `security-gates-merged.yml` (241 lines) — subset of `security-gates.yml` targeting `main`, `staging`, `production`

`security-gate.yml` is a strict subset of what `security-gates.yml` already does. `security-gates-merged.yml` overlaps with `security-gates.yml` on the `main` branch trigger.

**Why it matters:** Duplicate CI jobs waste runner minutes, slow PR feedback, and create confusion about which workflow is authoritative when one passes and another fails.
**Severity:** Medium
**Recommended fix:** 
1. Delete `security-gate.yml` — its `pytest tests/security/` step is already covered by `security-gates.yml`.
2. Merge `security-gates-merged.yml`'s unique jobs (if any) into `security-gates.yml` under a branch filter, then delete `security-gates-merged.yml`.
3. `security-gates.yml` becomes the single authoritative security workflow.
**Estimated effort:** Medium

---

### Category 6 — Backend: `print()` in Production Crawler Code

**Issue:** `services/layer1-ingestion/src/crawler/httpx_crawler.py` and `quality_gate.py` contain `print()` statements in production code paths (not migrations, not scripts).
**Why it matters:** `print()` bypasses structured logging (`structlog`), is invisible to log aggregators, and pollutes stdout in production containers.
**Severity:** Low
**Recommended fix:** Replace with `logger.debug(...)` using the existing `structlog` logger pattern already present in the same files.
**Estimated effort:** Small

---

### Category 7 — Config: Layer 6 Auth Bypass Flag Proliferation

**Issue:** `services/layer6-benchmarks/src/settings.py` defines **four** separate auth bypass flags (`ALLOW_INSECURE_DEV_AUTH_BYPASS`, `DEV_AUTH_BYPASS`, `AUTH_BYPASS_ENABLED`, `ALLOW_DEV_AUTH_BYPASS`) where other services use one (`ALLOW_INSECURE_DEV_AUTH_BYPASS`). All four are checked independently.
**Why it matters:** Four flags for the same concern means a security reviewer must check all four. Any one of them can enable bypass. This is a security surface expansion with no documented rationale.
**Severity:** Medium
**Recommended fix:** Consolidate to `ALLOW_INSECURE_DEV_AUTH_BYPASS` (the canonical flag used by Layer 5 and the shared package). Deprecate the other three with a startup warning. Update `.env.example` and `.env.dev.example`.
**Estimated effort:** Small

---

## Priority Plan

### Quick Wins (implement first — all low-risk, independently verifiable)

1. Delete `cleanup_pytest_cache.py`, `fix_all_relative_imports.py`, `fix_test_imports.py`
2. Add `compose-resolved.yml` to `.gitignore`
3. Remove dead paths from `pyrightconfig.json` `strict` array
4. Move `spec-oidc-audit.md` and `spec-test-report.md` to `specs/`
5. Update stale `contracts/drift-allowlist.yaml` `review_by` dates
6. Remove `"use client"` directives from `apps/web/src/`
7. Delete `components/layout/Layout.tsx` (dead code, 783 lines)
8. Replace `print()` with `logger.debug()` in Layer 1 crawler files
9. Consolidate Layer 6 auth bypass flags to single canonical flag

### Medium-Effort Structural Fixes (higher value, more files touched)

10. Migrate all 81 WfPrimitives callers to canonical imports, delete shim
11. Consolidate 3 security CI workflows into 1

### High-Risk / High-Value Refactors (deferred — see below)

- `app_monolith.py` splits (Layer 1: 3071 lines, Layer 3: 3836 lines)
- Layer 2.5 Signal Refinery architecture clarification (not in six-layer docs)
- `from src.` import pattern in Layer 4 tests (requires pytest pythonpath audit)
- Coverage floor gaps for Layers 1, 3, 5, 6

---

## Acceptance Criteria

1. `cleanup_pytest_cache.py`, `fix_all_relative_imports.py`, `fix_test_imports.py` do not exist in the repo root.
2. `compose-resolved.yml` is listed in `.gitignore`.
3. `pyrightconfig.json` `strict` array contains only `tests/layer3/test_typed_payloads.py`.
4. `spec-oidc-audit.md` and `spec-test-report.md` exist under `specs/`, not at repo root.
5. All `review_by` dates in `contracts/drift-allowlist.yaml` are in the future.
6. No `"use client"` directive exists in any file under `apps/web/src/`.
7. `apps/web/src/components/layout/Layout.tsx` does not exist; its export is removed from `components/index.ts`.
8. `services/layer1-ingestion/src/crawler/httpx_crawler.py` and `quality_gate.py` contain no bare `print()` calls.
9. `services/layer6-benchmarks/src/settings.py` defines only `ALLOW_INSECURE_DEV_AUTH_BYPASS`; the other three flags emit `DeprecationWarning` at startup if set.
10. No file under `apps/web/src/` imports from `@/components/WfPrimitives` (except `WfPrimitives.tsx` itself, which is then deleted).
11. `apps/web/src/components/WfPrimitives.tsx` does not exist.
12. `.github/workflows/security-gate.yml` and `.github/workflows/security-gates-merged.yml` do not exist; their coverage is absorbed into `security-gates.yml`.
13. `pnpm --dir apps/web build` passes with no TypeScript errors.
14. `pytest tests/ -x -q` passes (or fails only on pre-existing infra-gated tests).

---

## Implementation Approach

Steps are ordered by risk (lowest first) and independence (each step is verifiable on its own).

1. **Delete orphaned root scripts** — Remove `cleanup_pytest_cache.py`, `fix_all_relative_imports.py`, `fix_test_imports.py`. Verify no CI workflow references them.

2. **Gitignore compose-resolved.yml** — Add single line to `.gitignore`.

3. **Fix pyrightconfig.json** — Remove three dead `strict` paths. Keep `tests/layer3/test_typed_payloads.py`.

4. **Move working spec files** — `git mv spec-oidc-audit.md specs/` and `git mv spec-test-report.md specs/`. Update any internal links.

5. **Update drift-allowlist review dates** — Set all three `review_by` to `2026-08-18`. Add a comment noting the review outcome (SSE representation gap is accepted).

6. **Remove `"use client"` directives** — Strip from all 10 files. No behavior change in Vite.

7. **Delete Layout.tsx** — Confirm zero non-test imports, delete file, remove export from `components/index.ts`.

8. **Replace print() with logger.debug()** — In `httpx_crawler.py` and `quality_gate.py`, use the existing `structlog` logger.

9. **Consolidate Layer 6 auth bypass flags** — Keep `ALLOW_INSECURE_DEV_AUTH_BYPASS`. Add `DeprecationWarning` to the three legacy flag checks. Update `.env.dev.example` comment.

10. **Migrate WfPrimitives callers** — For each of the 81 importing files, replace `WfPrimitives` imports with canonical equivalents. Key mappings: `Btn` → `Button` from `@/components/ui/button`; `SectionCard` → `FabricCard` from `@/components/ui/fabric`; `MetricCard`, `StatusBadge`, `DataTable`, `PageHeader`, `EntityBadge` → `@/components/ui/fabric` or `@/components/blocks`. After all callers are migrated, delete `WfPrimitives.tsx` and remove its export from `components/index.ts`. Run `pnpm --dir apps/web build` to verify.

11. **Consolidate security CI workflows** — Audit `security-gates-merged.yml` for any jobs not in `security-gates.yml`. Merge unique jobs into `security-gates.yml` under appropriate branch filters. Delete `security-gate.yml` and `security-gates-merged.yml`. Verify the remaining workflow covers all previous triggers.

---

## Files Touched

| File | Change |
|---|---|
| `cleanup_pytest_cache.py` | Delete |
| `fix_all_relative_imports.py` | Delete |
| `fix_test_imports.py` | Delete |
| `.gitignore` | Add `compose-resolved.yml` |
| `pyrightconfig.json` | Remove 3 dead strict paths |
| `spec-oidc-audit.md` | Move to `specs/spec-oidc-audit.md` |
| `spec-test-report.md` | Move to `specs/spec-test-report.md` |
| `contracts/drift-allowlist.yaml` | Update 3 stale `review_by` dates |
| `apps/web/src/components/layout/GlobalLayout.tsx` | Remove `"use client"` |
| `apps/web/src/components/layout/AppHeader.tsx` | Remove `"use client"` |
| `apps/web/src/components/layout/LeftNavigation.tsx` | Remove `"use client"` |
| `apps/web/src/workflow/pages/ProspectSetup.tsx` | Remove `"use client"` |
| `apps/web/src/components/workspace/ProspectPromptBuilder.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/form.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/sheet.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/toggle-group.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/command.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/sidebar.tsx` | Remove `"use client"` |
| `apps/web/src/components/layout/Layout.tsx` | Delete |
| `apps/web/src/components/index.ts` | Remove `Layout` export; remove `WfPrimitives` export after migration |
| `services/layer1-ingestion/src/crawler/httpx_crawler.py` | Replace `print()` with `logger.debug()` |
| `services/layer1-ingestion/src/crawler/quality_gate.py` | Replace `print()` with `logger.debug()` |
| `services/layer6-benchmarks/src/settings.py` | Consolidate auth bypass flags |
| `.env.dev.example` | Update auth bypass flag comment |
| `apps/web/src/components/WfPrimitives.tsx` | Delete (after all callers migrated) |
| 81 files importing `WfPrimitives` | Migrate to canonical imports |
| `.github/workflows/security-gate.yml` | Delete |
| `.github/workflows/security-gates-merged.yml` | Delete (after merging unique jobs) |
| `.github/workflows/security-gates.yml` | Absorb coverage from deleted workflows |

---

## Deferred / Needs Decision

| Item | Why deferred | Decision needed | Recommended next step |
|---|---|---|---|
| `app_monolith.py` splits (L1: 3071 lines, L3: 3836 lines) | High churn, cross-cutting; splitting requires route ownership decisions | Which route groups move first? Who owns the split? | Create a dedicated spec per layer; start with L3 which already has a migration ledger |
| Layer 2.5 Signal Refinery (`services/layer2-5-signal-refinery/`) | Not documented in the six-layer architecture, not in k8s manifests, but present in `docker-compose.dev.yml` | Is this a permanent layer or a prototype? Should it be in the architecture docs? | Clarify ownership; add to ARCHITECTURE.md or mark as experimental |
| `from src.` imports in Layer 4 tests | Requires pytest `pythonpath` audit; could break test collection if changed naively | Is `pythonpath = ["src"]` in `pyproject.toml` the intended resolution? | Audit Layer 4 test collection with `pytest --collect-only`; fix import style in a dedicated pass |
| Coverage floors for Layers 1, 3, 5, 6 | Adding `fail_under` without knowing current coverage could immediately break CI | What is the current coverage for each layer? | Run `pytest --cov=src --cov-report=term-missing` per layer; set floors at current - 5% |
| `xfail(strict=False)` on cross-tenant write tests | These are security tests that are allowed to pass unexpectedly — masking regressions | Should cross-tenant write tests be `strict=True`? | Review each `xfail` reason; promote to `strict=True` where the underlying behavior is now implemented |
| Layer 6 `DEV_AUTH_BYPASS` / `AUTH_BYPASS_ENABLED` full removal | Removing env vars could break existing deployment configs silently | Are these flags set in any deployment environment? | Audit k8s secrets and `.env` files in deployment environments before removing |
