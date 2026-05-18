# Spec: Sprint 0 — Release Truth, Repo Stabilization, and Agent Operating Plan

## Status
Ready for implementation

---

## Problem Statement

Sprint 0 closes the remaining known blockers before a controlled pilot launch. Several items from the prior production-readiness spec are already implemented (kustomization.yaml cleaned, template exists, digest guard script exists, `database.py` fixed to 422 + DeprecationWarning, compatibility-debt-registry Vault entry exists). This spec covers only the **remaining open gaps** and the **new Sprint 0 deliverables**.

### Open gaps (implementation required)

1. **Layer 3 `manager.py` — `VaultSourceNotSupportedError` not defined.** The existing test `test_vault_config_source.py` imports `VaultSourceNotSupportedError` from `value_fabric.layer3.config.manager` (which resolves to `services/layer3-knowledge/src/config/manager.py`). That class does not exist there. `_load_from_vault()` still returns `{}` instead of raising. The test suite cannot pass until the implementation matches the release spec.

2. **Digest guard not wired into CI.** `scripts/check-no-placeholder-digests.sh` exists but is not referenced in `.github/workflows/environment-promotion.yml`. Placeholder digests can still reach staging or prod without a CI gate.

### New Sprint 0 deliverables

3. **`reports/launch-readiness-sprint0.md`** — A durable evidence artifact capturing commands run, test results, known failures classified by type, coverage, and release gate status.

4. **`docs/readiness/blockers.md`** — Living launch blocker board (P0/P1/P2), referenced from the sprint report.

5. **ROADMAP.md reconciliation** — Add a canonical-source note near the top of ROADMAP.md so the stale 95% figure is not mistaken for the current readiness value. Do not change the percentage; `docs/readiness/current.md` (97%) is canonical.

---

## Requirements

### R1 — Fix `manager.py`: define `VaultSourceNotSupportedError` and raise it

| ID | Requirement |
|---|---|
| R1.1 | Define `class VaultSourceNotSupportedError(RuntimeError)` in `services/layer3-knowledge/src/config/manager.py`. |
| R1.2 | `_load_from_vault()` must raise `VaultSourceNotSupportedError` with a message that names the source and references ESO/environment-backed config as the migration path. It must not return `{}`. |
| R1.3 | The existing test `services/layer3-knowledge/tests/test_vault_config_source.py` must pass without modification. |
| R1.4 | Add a regression test only if the existing test does not verify both the exception type and the message content. (Audit first; add only if needed.) |
| R1.5 | `docs/governance/compatibility-debt-registry.md` already documents this as intentional v1 behavior — confirm the entry is accurate and update only if the implementation diverges from what is documented. |

### R2 — Wire digest guard into environment-promotion CI

| ID | Requirement |
|---|---|
| R2.1 | Add a `Block placeholder image digests` step in `.github/workflows/environment-promotion.yml` before the staging deploy step. |
| R2.2 | Add the same step before the production deploy step. |
| R2.3 | The step must run `bash scripts/check-no-placeholder-digests.sh k8s/envs/<env>/kustomization.yaml` where `<env>` is `staging` or `prod` respectively. |
| R2.4 | The step must fail the job (exit non-zero) if placeholder digests are found, blocking the deploy. |

### R3 — Sprint 0 launch-readiness report

| ID | Requirement |
|---|---|
| R3.1 | Create `reports/launch-readiness-sprint0.md`. |
| R3.2 | Report must include: commands run, test pass/fail counts per suite (from the 2026-05-17 test report or a fresh run), known failures classified as: implementation failure / environment issue / pre-existing unrelated failure. |
| R3.3 | Report must include per-layer coverage figures. |
| R3.4 | Report must state whether release gates are green or blocked, with evidence. |
| R3.5 | Report must include a "Sprint 0 Blockers Snapshot" section with P0/P1/P2 open counts and a link to `docs/readiness/blockers.md`. |
| R3.6 | Report must not claim gates are green unless `make verify` (or the closest available subset) was actually run and passed. |

### R4 — Launch blocker board

| ID | Requirement |
|---|---|
| R4.1 | Create `docs/readiness/blockers.md`. |
| R4.2 | Board must have three sections: **P0 — Release blockers**, **P1 — Must fix before external demo**, **P2 — Post-launch hardening**. |
| R4.3 | Each section must use a table with columns: ID, Area, Blocker/Item, Owner, Status, Evidence/Link. |
| R4.4 | Populate from existing audit evidence: `reports/RELEASE_READINESS_AUDIT_2026-05-12.md` is the primary source for known P0/P1/P2 items. |
| R4.5 | Include a `_Last updated:` datestamp at the top. |
| R4.6 | P0 definition: release-blocking (pilot cannot launch). P1 definition: must fix before external demo. P2 definition: post-launch hardening. |

### R5 — ROADMAP.md canonical-source note

| ID | Requirement |
|---|---|
| R5.1 | Add or strengthen a note near the top of ROADMAP.md (within the first 20 lines or immediately after the executive summary header) stating that `docs/readiness/current.md` is the canonical source for launch readiness and that any percentage in ROADMAP.md is historical/contextual. |
| R5.2 | Do not change the 95% figure in ROADMAP.md. |
| R5.3 | Do not change the 97% figure in `docs/readiness/current.md`. |

---

## Acceptance Criteria

1. `pytest services/layer3-knowledge/tests/test_vault_config_source.py` passes (all tests green).
2. `VaultSourceNotSupportedError` is defined in `services/layer3-knowledge/src/config/manager.py`.
3. `_load_from_vault()` raises `VaultSourceNotSupportedError`; it does not return `{}`.
4. `.github/workflows/environment-promotion.yml` contains a `Block placeholder image digests` step before both the staging and production deploy steps.
5. `reports/launch-readiness-sprint0.md` exists and contains: commands run, test counts, failure classifications, coverage, gate status, and a blocker snapshot with link.
6. `docs/readiness/blockers.md` exists with P0/P1/P2 tables populated from audit evidence.
7. ROADMAP.md contains a note that `docs/readiness/current.md` is canonical; the 95% figure is not changed.
8. `docs/readiness/current.md` is unchanged (97% remains canonical).
9. No new test files are added unless the existing vault test is found to be insufficient after inspection.

---

## Implementation Approach

Steps are ordered by dependency. Each step is independently verifiable.

1. **Fix `manager.py`** — Add `VaultSourceNotSupportedError(RuntimeError)` class. Change `_load_from_vault()` to raise it with a message naming the source and the ESO migration path. Confirm the compatibility-debt-registry entry matches.

2. **Run vault tests** — Execute `pytest services/layer3-knowledge/tests/test_vault_config_source.py -v` and confirm all tests pass. If any test fails for a reason other than the implementation gap, investigate before proceeding.

3. **Wire digest guard into CI** — Edit `.github/workflows/environment-promotion.yml`. Locate the staging deploy step and insert the guard immediately before it. Repeat for the production deploy step. Use `bash scripts/check-no-placeholder-digests.sh k8s/envs/staging/kustomization.yaml` and `k8s/envs/prod/kustomization.yaml` respectively.

4. **Run `make verify` (or closest available subset)** — Capture output. Note which targets pass, which fail, and classify failures. This output feeds the sprint report.

5. **Create `docs/readiness/blockers.md`** — Populate P0/P1/P2 tables from `reports/RELEASE_READINESS_AUDIT_2026-05-12.md` and the 2026-05-17 test report. Use the P0/P1/P2 definitions from the spec.

6. **Create `reports/launch-readiness-sprint0.md`** — Write the evidence artifact using the output from steps 2, 3, and 4. Include the blocker snapshot (open counts + link to `docs/readiness/blockers.md`).

7. **Reconcile ROADMAP.md** — Add the canonical-source note. Do not change any percentage.

8. **Final verification** — Re-run `pytest services/layer3-knowledge/tests/test_vault_config_source.py` to confirm green. Confirm `environment-promotion.yml` diff is correct. Confirm all new files exist.

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
| `services/layer3-knowledge/src/config/manager.py` | Add `VaultSourceNotSupportedError`; change `_load_from_vault()` to raise it |
| `.github/workflows/environment-promotion.yml` | Add digest guard step before staging + prod deploy steps |
| `docs/readiness/blockers.md` | New — P0/P1/P2 launch blocker board |
| `reports/launch-readiness-sprint0.md` | New — Sprint 0 evidence artifact |
| `ROADMAP.md` | Add canonical-source note (no percentage change) |

### Files confirmed already done — no changes needed

| File | Status |
|---|---|
| `k8s/envs/prod/kustomization.yaml` | ✅ Placeholder digests already removed |
| `k8s/envs/prod/kustomization.yaml.template` | ✅ Already exists with `<resolved-by-ci>` markers |
| `scripts/check-no-placeholder-digests.sh` | ✅ Already exists and correct |
| `docs/governance/compatibility-debt-registry.md` | ✅ Vault v1 release note already present |
| `services/layer4-agents/src/database.py` | ✅ Already uses 422 + DeprecationWarning |
| `services/layer4-agents/tests/test_isolation_tier_provisioning.py` | ✅ Tests already cover 422 + deprecation |

---

## Known Pre-existing Failures (not Sprint 0 scope)

From the 2026-05-17 test report — these are pre-existing and must be classified in the sprint report but not fixed in Sprint 0:

- 17 test collection errors (import topology, missing modules, f-string syntax error)
- Layer 1: 117 failures, 99 errors (mostly testcontainers/Docker unavailable)
- Layer 3: 41 failures, 3 errors (Prometheus registry collision, graph alias export missing)
- Layer 4: 231 failures, 98 errors (infrastructure unavailable)
- Layer 5: 21 failures, 101 errors (testcontainers)
- Frontend: 100 failures (Vitest)

These are environment issues or pre-existing implementation gaps, not regressions introduced by Sprint 0 work.
