# DEPRECATED: Root shared/ Directory

**Status:** Deprecated - Pending Removal  
**Replacement:** `value-fabric/shared/`  
**Date:** 2026-04-19

## Migration Notice

The root `shared/` directory is deprecated and will be removed. All shared packages have been consolidated into `value-fabric/shared/` which is the canonical location.

## Migration Path

Update imports from:
```python
from shared.identity import ...
```

To:
```python
from shared.identity import ...  # (same import, but from value-fabric/shared/)
```

## Blockers for Full Consolidation

To complete consolidation, ensure:
1. All layers have their `pyproject.toml` updated to include `value-fabric/shared/` in package search paths
2. All imports in layer1-4 use the canonical shared package
3. Root `shared/` is removed after verification

## Files Present in Root (Deprecated)

- `identity/` - Identity and governance (superseded by value-fabric/shared/identity/)
- `audit/` - Audit logging (superseded by value-fabric/shared/audit/)
- `secrets/` - Secrets management (superseded by value-fabric/shared/secrets/)
- `security/` - Security middleware (superseded by value-fabric/shared/security/)
- `tracing/` - Distributed tracing (superseded by value-fabric/shared/tracing/)
