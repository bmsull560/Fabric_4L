# Deprecation Inventory

This document provides a human-readable view of scheduled deprecations and removals. The source of truth is `docs/deprecation_register.json`.

## Current Deprecations

| Feature | Introduced | Deprecated Since | Target Removal | Owner | Path |
|---------|------------|------------------|----------------|-------|------|

*No active deprecations.*

---

## Deprecation Policy

### Timeline

- **Deprecation announcement**: Feature marked as deprecated with at least 90 days notice
- **Migration period**: 60-90 days for consumers to update
- **Target removal**: Feature removed on target date

### Communication

1. Deprecation added to `docs/deprecation_register.json`
2. Warning headers added to API responses
3. Documentation updated with migration guide
4. CI gate fails on overdue deprecations

### Headers

Deprecated endpoints return:

- `Warning: 299 - "Deprecated since {date}"` (RFC 7234)
- `X-Deprecated-Since: {ISO date}`
- `X-Target-Removal-Date: {ISO date}`
- `X-Deprecation-Owner: {team email}`

---

## CI Gate

The `check-deprecations` make target and CI job enforce removal deadlines:

```bash
# Check deprecations (fails on overdue)
make check-deprecations

# Bypass (not recommended for production)
DEPRECATION_ALLOW_OVERDUE=true make check-deprecations
```

---

## Adding a New Deprecation

1. Edit `docs/deprecation_register.json`:

```json
{
  "deprecations": [
    {
      "feature": "legacy-api-v1",
      "introduced": "2024-01-01",
      "deprecated_since": "2026-04-01",
      "target_removal": "2026-07-01",
      "owner": "platform-team@valuefabric.io",
      "path": "/api/v1/legacy"
    }
  ]
}
```

2. Instrument the endpoint in Layer 1 or Layer 3 to emit deprecation headers
3. Update this inventory file
4. Notify affected teams

---

## Historical Removals

| Feature | Deprecated | Removed | Migration Path |
|---------|------------|---------|----------------|

*No historical removals yet.*

---

## Related Documentation

- [API Reference](API_REFERENCE.md) - API documentation
- [Semantic Contract](semantic_contract.md) - Breaking change policy
- [Deprecation Register](deprecation_register.json) - Machine-readable source
