# Enterprise OIDC / SSO Incident Runbook

This runbook covers enterprise identity-provider incidents affecting Fabric_4L user login, tenant mapping, token validation, and session lifecycle behavior. It assumes local password fallback is disabled for production enterprise tenants unless an explicitly approved break-glass procedure is active.

## Severity Classification

| Severity | Condition | Expected response |
|---|---|---|
| SEV-1 | All enterprise users cannot authenticate, callback validation fails globally, or token signature validation is broken. | Page on-call immediately, freeze identity-related deployments, and keep authentication fail-closed. |
| SEV-2 | One tenant or provider integration is degraded, tenant mapping fails, or logout/session expiry is inconsistent. | Notify tenant owner, route incident to identity steward, and preserve audit evidence. |
| SEV-3 | Non-production provider metadata, documentation, or configuration drift is detected. | Open a tracked remediation ticket and validate before next release. |

## Immediate Checks

Confirm whether the provider discovery document, JWKS endpoint, authorization endpoint, token endpoint, and callback route are reachable from the deployment network. Do not paste provider secrets into logs or tickets. Capture only sanitized provider URL, HTTP status, request ID, tenant ID, and timestamp.

Canonical runtime auth boundaries and integration points:
- Shared identity boundary: `packages/shared/src/value_fabric/shared/identity/` (JWT decode, JWKS resolution, auth context, middleware, dependency gates).
- Service middleware entrypoints: each service `api/main.py` (or equivalent) where `GovernanceMiddleware` is mounted.
- Layer 4 OAuth callback boundary: `services/layer4-agents/src/api/routes/integrations.py` (`/v1/integrations/salesforce/oauth/callback`).

Configuration and secret-management guardrail:
- Keep `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`/`OIDC_JWKS_JSON`, and callback state-signing secrets in Infisical/Vault (or ExternalSecrets-backed injection), not in repo-tracked environment files.
- `.env.example` documents contract keys only; production values must come from secret manager paths.

| Check | Command or evidence | Pass criterion |
|---|---|---|
| Discovery metadata | Fetch configured issuer metadata from the deployment environment. | HTTP 200 and issuer matches configured issuer exactly. |
| JWKS | Fetch configured JWKS URI. | HTTP 200 and active key ID matches token header. |
| Callback route | Exercise authorization-code callback in staging or break-glass diagnostic flow. | State, nonce, PKCE, signature, audience, expiry, and tenant mapping pass. |
| Audit emission | Query audit events for login success/failure. | Auth events include tenant, subject hash, provider, and outcome. |

## Remediation Procedure

Keep authentication fail-closed while diagnosing signature, issuer, audience, or tenant-claim mismatches. If a provider key rotation caused the incident, refresh JWKS cache and confirm the old and new key IDs are handled according to provider policy. If tenant mapping fails, disable only the affected tenant mapping and require explicit allow-list review before re-enabling fallback claims such as `org_id` or `hd`.

## Closure Evidence

The incident can close only after the affected tenant can complete login and logout, the callback route validates claims with the current provider keys, audit events exist for success and failure paths, and the post-incident review links the root cause to a preventive control.
