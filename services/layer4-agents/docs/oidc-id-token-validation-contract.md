# OIDC ID Token Validation Contract (Layer 4 Agents)

This service enforces strict ID token verification for OIDC callbacks.

## Required Claims

The `id_token` must include:

- `sub` (subject)
- `iss` (issuer)
- `aud` (audience)
- `exp` (expiry)
- `iat` (issued-at)
- `nonce` when nonce was issued at auth start

## Validation Rules

1. **Signature verification**: JWT signature must validate against the tenant's configured `jwks_uri` and matching `kid`.
2. **Algorithm allowlist**: only asymmetric algorithms are accepted (`RS256/384/512`, `ES256/384/512`).
3. **Issuer check**: `iss` must exactly equal the tenant-scoped configured issuer.
4. **Audience check**: `aud` must include or equal the tenant-scoped configured client_id.
5. **Time checks**:
   - `exp` must be in the future.
   - `iat` cannot be in the future (beyond clock skew) and must be within accepted staleness window.
6. **Nonce linkage**: callback token nonce must match stored nonce.
7. **State linkage**: callback state must match stored state; mismatch is treated as replay/mix-up.
8. **Tenant mapping**: issuer/client mapping is strict per tenant to prevent cross-tenant provider-configuration bleed.

## Failure Error Codes

API consumers should treat these as stable machine-readable categories:

- `oidc.id_token.invalid_format`
- `oidc.id_token.invalid_alg`
- `oidc.id_token.missing_kid`
- `oidc.id_token.stale_jwks`
- `oidc.id_token.invalid_jwk`
- `oidc.id_token.expired`
- `oidc.id_token.invalid_aud`
- `oidc.id_token.invalid_iss`
- `oidc.id_token.invalid_signature`
- `oidc.id_token.invalid_iat`
- `oidc.id_token.stale_iat`
- `oidc.id_token.invalid_nonce`
- `oidc.state.replay_or_mismatch`
- `oidc.tenant.invalid_issuer_mapping`
- `oidc.tenant.invalid_client_mapping`
