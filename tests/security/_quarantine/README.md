# Quarantined Tests

These tests were moved here because they **cannot collect** — they import
functions, classes, or modules that do not exist in the current codebase.

They were written against an API surface that was either never implemented or
was refactored away. The old gate system silently skipped them, which masked
the fact that they provided zero coverage.

## Specific Issues

| File | Root Cause |
|------|-----------|
| `test_jwt_security.py` | Imports `_DEFAULT_JWT_SECRET` from `shared.identity.jwt` — no such export |
| `test_middleware_security.py` | Imports `_build_context_from_role` from `shared.identity.middleware` — no such function |
| `test_rbac_permissions.py` | Imports `get_current_context` from `shared.identity.dependencies` — no such function |
| `test_api_key_security.py` | Imports non-existent `value_fabric` package |
| `test_auth_integration.py` | Imports non-existent `value_fabric` package |
| `test_oidc_pkce.py` | Relative import chain breaks: `tenants.models.api_key` → `...database` beyond top-level |

## Resolution

Each test should be either:
1. **Rewritten** against the actual codebase API (preferred)
2. **Deleted** if the capability it tests is already covered by the gate tests

Do **not** move these back to `tests/security/` until they can collect and pass.
The `_quarantine` prefix with underscore ensures pytest ignores this directory
by default.
