# DEPRECATED: Root shared/ Directory

**Status:** Completed - Root directory removed
**Replacement:** `packages/shared/src/value_fabric/shared/`
**Date:** 2026-04-19

## Migration Notice

The root `shared/` directory has been removed. All shared packages are consolidated into `packages/shared/src/value_fabric/shared/`, which is now the only supported location.

## Migration Path

Update imports from:
```python
from shared.identity import ...
```

To:
```python
from shared.identity import ...  # (same import, but from packages/shared/src/value_fabric/shared/)
```

## Blockers for Full Consolidation

To complete consolidation, ensure:
1. All layers have their `pyproject.toml` updated to include `packages/shared/src/value_fabric/shared/` in package search paths
2. All imports in layer1-4 use the canonical shared package
3. Root `shared/` is removed after verification

## Root Compatibility Status

No root `shared/` modules remain. All imports must resolve through `value_fabric.shared.*` from `packages/shared/src`.
