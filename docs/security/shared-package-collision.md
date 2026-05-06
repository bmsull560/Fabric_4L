# ADR: Shared Package Namespace Collision

## Status
Accepted — short-term warning comments added; long-term rename recommended.

## Context
The repository contains **two independent Python packages** named `shared`:

1. `shared/` (repo root)
   - Used by repo-wide scripts and utilities.
   - Contains: `crypto`, `governance`, `rate_limiting`, `llm_safety`, `observability`.
   - Security middleware: simpler, URL-encoded-style patterns.

2. `packages/shared/src/value_fabric/shared/`
   - Used by Layer 1–6 applications and all pytest suites.
   - Contains: `models`, `boundaries`, `mcp_gateway`, `secrets`, `security`, `testability`.
   - Security middleware: comprehensive `BaseHTTPMiddleware` with body caching, JSON validation, RDF exemptions.

Both packages have a `security/middleware.py` module with **different implementations**.
Layer 2 tests import via `sys.path.insert(0, "value-fabric")` (see `tests/security/test_shared_security_middleware.py`), so they resolve to the authoritative application middleware. Root-level scripts that run `import shared` from the repo root resolve to the root package.

## Decision
- **Short term:** Keep both packages but add prominent header comments and an import-path guard test so developers do not patch the wrong file during a security incident.
- **Long term:** Rename or consolidate. Options:
  1. Rename root `shared` → `platform_shared` or `repo_shared`.
  2. Merge root modules into `packages/shared/src/value_fabric/shared/` and delete the root package.
  3. Make `packages/shared/src/value_fabric/shared/` the only `shared` package and move repo-wide utilities elsewhere.

## Consequences
- **Risk:** A developer editing `shared/security/middleware.py` at the repo root may believe they are hardening the application, but Layer 2+ runtime imports `packages/shared/src/value_fabric/shared/security/middleware.py`.
- **Mitigation:** The import-path test (`TestMiddlewareImportPath`) will fail if pytest ever resolves the root package.
- **Follow-up:** Open a ticket to execute the rename/consolidation before the next security sprint.
