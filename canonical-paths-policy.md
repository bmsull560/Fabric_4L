# Canonical Path Authority Policy

This policy complements `canonical-paths.yaml` and defines authoritative trees for runtime code.

## Authoritative trees

- **Layer runtime code (Layers 1-6):** `services/layer*-*/src/` is authoritative.
- **Shared runtime libraries:** `packages/shared/` is authoritative.
- **Cross-service reusable packages:** `packages/` is authoritative for package modules.
- **App runtime UI:** `apps/web/` is authoritative.

## Non-authoritative mirrors and legacy trees

- `value_fabric/layer*/` is non-authoritative and must not be treated as source-of-truth for runtime edits.
- Any temporary duplicate tree must be removed after migration; CI strict duplicate checks are blocking.

## Import policy

- Runtime Python imports must use `value_fabric.shared...`.
- Root-level `shared` imports are prohibited in runtime paths (`services/`, `packages/`).

## CI enforcement

- `scripts/ci/check_duplicate_source_trees.py --strict` is a blocking gate for production branches.
- `scripts/ci/check_shared_imports.py --strict --scope runtime` is a blocking gate for runtime code.
- PR diff summary artifacts must include newly introduced violations to prevent silent drift.
