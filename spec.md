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
