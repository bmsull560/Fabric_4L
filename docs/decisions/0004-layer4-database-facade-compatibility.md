# ADR-0004: Layer 4 Database Facade Compatibility

- **Status**: accepted
- **Date**: 2024-01-15
- **Deciders**: Security Hardening Team
- **Stakeholders**: Layer 4 Agents Team, Infrastructure Team, Security Audit

## Context

`value_fabric.layer4.database` (the fail-safe database facade layer) was missing two key exports:

1. **`Base`** -- the SQLAlchemy declarative base class
2. **`TenantContextError`** -- the exception type raised on invalid or missing tenant context

This caused import failures in security tests that referenced these symbols but did not need real database connections:

```python
# Failure 1
ImportError: cannot import name 'Base' from 'value_fabric.layer4.database'

# Failure 2
AttributeError: module 'value_fabric.layer4.database' has no attribute 'TenantContextError'
```

The facade was intended to provide a fail-safe boundary: tests and consuming code should be able to import the module and its types without requiring a live database. The missing exports broke that contract.

## Decision

Restore fail-safe compatibility exports for `Base` and `TenantContextError` in `value_fabric.layer4.database`. Additionally, restore `get_db_from_context` as a delegated export only.

### File changed

- `value_fabric/layer4/database_facade.py`
  - Added export: `Base` -- the SQLAlchemy declarative base
  - Added export: `TenantContextError` -- exception raised when tenant context is invalid or missing
  - Added delegated export: `get_db_from_context` -- forwards to the canonical database module; does not create a fallback unscoped session

### Behavior preserved

- **Invalid or missing tenant context** still raises `TenantContextError` with the expected exception type
- **No unscoped DB session fallback** -- the facade never returns a database session outside of a valid tenant context
- **Fail-safe behavior** is maintained: importing the module does not require a database connection

## Consequences

### Positive
- Multiple security tests become importable and pass without requiring live database infrastructure
- `TenantContextError` is now catchable by its canonical type in test assertions
- `Base` can be used for model registration and type checking
- Restores the facade's contract as a safe import boundary

### Negative / Risks
- Delegated exports create a thin forwarding layer; if the canonical module changes symbol names, the facade must be updated
- `get_db_from_context` as a delegated export only means callers still need a valid context; no convenience fallback

### Neutral
- No changes to the actual database connection logic
- No changes to tenant context validation rules
- The facade continues to be a thin compatibility layer

## Validation

After restoring the exports, the following security tests became importable and pass:

```bash
# WebSocket auth test (also needs JWT decoder fix from ADR-0001)
python -m pytest tests/security/test_p1_13_websocket_auth.py -n 0 --maxfail=1 -vv
```
**Expected:** 3 passed

```bash
# Tenant validation metrics test
python -m pytest tests/security/test_tenant_validation_metrics.py -n 0 --maxfail=1 -vv
```
**Expected:** all tests pass (module is now importable)

```bash
# Security fixes test -- cypher write operations
python -m pytest tests/security/test_security_fixes.py -n 0 --maxfail=1 -vv
```
**Expected:** all tests pass (module is now importable)

## Related
- Related ADRs:
  - [ADR-0001: WebSocket JWT Canonical Decoder](0001-websocket-jwt-canonical-decoder.md) -- both fix Layer 4 contract/export issues; `test_p1_13_websocket_auth.py` depends on both
- Related files:
  - `value_fabric/layer4/database_facade.py`
  - `tests/security/test_p1_13_websocket_auth.py`
  - `tests/security/test_tenant_validation_metrics.py`
  - `tests/security/test_security_fixes.py`
- Related tests:
  - `python -m pytest tests/security/test_p1_13_websocket_auth.py -n 0 --maxfail=1 -vv`
  - `python -m pytest tests/security/test_tenant_validation_metrics.py -n 0 --maxfail=1 -vv`
  - `python -m pytest tests/security/test_security_fixes.py -n 0 --maxfail=1 -vv`
