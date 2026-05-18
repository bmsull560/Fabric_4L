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
