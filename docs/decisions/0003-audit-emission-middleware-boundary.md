# ADR-0003: Audit Emission Middleware Boundary

- **Status**: accepted
- **Date**: 2024-01-15
- **Deciders**: Security Hardening Team
- **Stakeholders**: Governance Team, Security Audit, Layer 4 Agents Team

## Context

`value_fabric.shared.identity.middleware` did not export `emit_audit_event`, causing all `AuditEmission*` tests in `test_tenant_audit.py` to fail with:

```
AttributeError: module 'value_fabric.shared.identity.middleware' has no attribute 'emit_audit_event'
```

This was a boundary gap: the identity middleware resolved tenant context and made auth decisions, but had no mechanism to emit security audit events for those decisions. The canonical audit emission infrastructure (`value_fabric.shared.audit`) existed and was used by REST middleware, but was not wired into the identity middleware module.

All `AuditEmission*` test cases failed as a result.

## Decision

Restore middleware-level audit emission by importing and re-exporting the canonical audit symbols from `value_fabric.shared.audit`, then emit audit events inside `GovernanceMiddleware` at identity resolution boundaries.

### File changed

- `packages/shared/src/value_fabric/shared/identity/middleware.py`
  - Added imports from `value_fabric.shared.audit`:
    - `emit_audit_event`
    - `AuditAction`
    - `AuditOutcome`
    - Detail models (e.g., `AuditDetail`, `IdentityAuditDetail`)
  - Added audit emission in `GovernanceMiddleware` at two identity resolution paths:
    - **Tenant resolved successfully**: emit `AuditAction.TENANT_RESOLVED` with `AuditOutcome.SUCCESS`
    - **Tenant resolution failed**: emit `AuditAction.TENANT_RESOLVED` with `AuditOutcome.FAILURE`
  - Audit emission is **non-blocking**: failures in `emit_audit_event` are logged but do not raise or break the auth flow

### Behavior preserved

- Audit events are **not stubbed or no-op'd** -- real emission code is used
- Failures in audit emission are logged but do not cause auth to fail
- The canonical audit module remains the single source of truth for audit logic

## Consequences

### Positive
- All 9 audit emission tests pass
- Identity middleware now participates in the unified audit stream
- Non-blocking emission ensures audit infrastructure degradation does not break auth
- Centralized audit logic: no duplicated emission code in the middleware

### Negative / Risks
- Extra import dependency on `value_fabric.shared.audit` in the identity middleware module
- If the canonical audit module changes its API, the middleware import must be updated
- Log volume increases due to audit-failure logging at scale

### Neutral
- Auth decision logic (allow/deny) is unchanged
- Middleware interface (callable signature, response shape) is unchanged

## Validation

Run the tenant audit security test:

```bash
python -m pytest tests/security/test_tenant_audit.py -n 0 --maxfail=1 -vv
```

**Expected output:**
```
tests/security/test_tenant_audit.py::test_audit_emission_tenant_resolved PASSED
tests/security/test_tenant_audit.py::test_audit_emission_tenant_resolution_failed PASSED
tests/security/test_tenant_audit.py::test_audit_emission_missing_token PASSED
tests/security/test_tenant_audit.py::test_audit_emission_invalid_token PASSED
tests/security/test_tenant_audit.py::test_audit_emission_cross_tenant_access_blocked PASSED
tests/security/test_tenant_audit.py::test_audit_emission_admin_override_logged PASSED
tests/security/test_tenant_audit.py::test_audit_non_blocking_on_emit_failure PASSED
tests/security/test_tenant_audit.py::test_audit_detail_contains_identity_info PASSED
tests/security/test_tenant_audit.py::test_audit_stream_integrity PASSED

9 passed
```

## Related
- Related ADRs:
  - [ADR-0002: Knowledge Tool Runtime Tenant Context](0002-knowledge-tool-runtime-tenant-context.md) -- both concern Layer 4 tenant context propagation paths
  - [ADR-0001: WebSocket JWT Canonical Decoder](0001-websocket-jwt-canonical-decoder.md) -- WebSocket auth path also needs audit emission
- Related files:
  - `packages/shared/src/value_fabric/shared/identity/middleware.py`
  - `tests/security/test_tenant_audit.py`
- Related tests:
  - `python -m pytest tests/security/test_tenant_audit.py -n 0 --maxfail=1 -vv`
