# DEPRECATED: Root shared/ Directory

**Status:** Deprecated - Pending Removal
**Replacement:** `packages/shared/src/value_fabric/shared/`
**Date:** 2026-04-19

## Migration Notice

The root `shared/` directory is deprecated and will be removed. All shared packages have been consolidated into `packages/shared/src/value_fabric/shared/` which is the canonical location.

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

## Files Present in Root (Deprecated)

- `identity/` - Identity and governance (superseded by packages/shared/src/value_fabric/shared/identity/)
- `audit/` - Audit logging (superseded by packages/shared/src/value_fabric/shared/audit/)
- `secrets/` - Secrets management (superseded by packages/shared/src/value_fabric/shared/secrets/)
- `security/` - Security middleware (superseded by packages/shared/src/value_fabric/shared/security/)
- `tracing/` - Distributed tracing (superseded by packages/shared/src/value_fabric/shared/tracing/)
