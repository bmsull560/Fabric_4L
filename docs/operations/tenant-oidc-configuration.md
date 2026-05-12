# Tenant OIDC Configuration Guide

This document explains how to configure OIDC-based single sign-on for tenants in Fabric 4L. The platform uses a generic OIDC client (`shared/identity/oidc.py`) that supports any compliant identity provider.

---

## 1. Overview

Fabric 4L authenticates tenant users via the OpenID Connect protocol. Each tenant can bring its own OIDC-compliant identity provider (IdP).

**Recommended default:** [Keycloak](./keycloak-integration.md) — self-hosted, enterprise-ready, supports identity brokering for Google/Apple/Entra ID.

The platform does not automate IdP realm creation; instead, tenant administrators configure their IdP independently and register the OIDC settings through the provisioning pipeline or admin API.

### Supported Identity Providers

| Provider | Tested | Notes |
|----------|--------|-------|
| Keycloak | Yes | Self-hosted; recommended for on-prem deployments |
| Auth0 | Yes | SaaS; supports Organizations for multi-tenant |
| Okta | Yes | Enterprise SSO; supports custom claims |
| Azure AD / Entra ID | Yes | Microsoft ecosystem; use App Registration |
| Google | Yes | Standard OIDC; preset endpoints available |
| Apple Sign In | Yes | Requires JWT client-secret generation |
| Any OIDC-compliant IdP | Expected | Must support discovery endpoint |

---

## 2. Prerequisites

Before configuring OIDC for a tenant, ensure:

1. The tenant has been provisioned (status = `active`) via the provisioning pipeline.
2. The tenant's Infisical secret path exists at `/tenants/{tenant-id}/`.
3. The tenant administrator has access to their IdP's admin console.

---

## 3. Identity Provider Setup

### 3.1 Create an OIDC Application in Your IdP

In your identity provider's admin console, create a new application with these settings:

| Setting | Value |
|---------|-------|
| **Application Type** | Regular Web Application (Confidential Client) |
| **Grant Types** | Authorization Code with PKCE |
| **Allowed Callback URLs** | `https://{your-domain}/api/v1/auth/oidc/callback` |
| **Allowed Logout URLs** | `https://{your-domain}/` |
| **Token Endpoint Auth** | `client_secret_post` or `client_secret_basic` |

### 3.2 Configure Required Claims

The ID token **must** include these claims:

| Claim | Required | Description |
|-------|----------|-------------|
| `sub` | Yes | Unique user identifier within the IdP |
| `email` | Yes | User's email address |
| `name` | Recommended | Display name |
| `tenant_id` | Recommended | Must match the Fabric 4L tenant UUID (custom claim) |
| `roles` or `groups` | Recommended | Used for role mapping via `map_role_from_claims()` |

If your IdP does not support a custom `tenant_id` claim, the platform resolves the tenant from the OIDC client configuration (each tenant has its own client ID).

### 3.3 Note Your Configuration Values

After creating the application, record:

- **Issuer URL** (e.g., `https://auth.example.com/realms/my-tenant`)
- **Client ID**
- **Client Secret**
- **Discovery URL** (usually `{issuer_url}/.well-known/openid-configuration`)

### 3.4 Google and Apple Sign-In Setup

For **Google** and **Apple**, the platform provides preset endpoints so you can omit `issuer_url` and most endpoint fields.

#### Google OAuth 2.0

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Web application type)
3. Add authorized redirect URI: `https://{your-domain}/api/v1/auth/oidc/callback`
4. Note the **Client ID** and **Client Secret**
5. Enable the **Google People API** (for `profile` scope)

Required tenant settings:
```json
{
  "oidc": {
    "provider_name": "google",
    "client_id": "YOUR_GOOGLE_CLIENT_ID",
    "client_secret_ref": "OIDC_CLIENT_SECRET_GOOGLE",
    "auto_provision_users": true,
    "default_role": "read_only"
  }
}
```

#### Apple Sign In

1. Go to [Apple Developer Portal](https://developer.apple.com/) → Certificates, Identifiers & Profiles
2. Create an **App ID** with "Sign In with Apple" capability
3. Create a **Services ID** for the web application
4. Configure the **Return URL** (redirect URI): `https://{your-domain}/api/v1/auth/oidc/callback`
5. Create a **Sign In with Apple** private key (ES256, .p8 format)
6. Note the **Team ID**, **Key ID**, **Services ID** (used as `client_id`), and download the private key

Required tenant settings:
```json
{
  "oidc": {
    "provider_name": "apple",
    "client_id": "com.example.webapp",
    "auto_provision_users": true,
    "default_role": "read_only"
  }
}
```

Required environment variables (or Infisical secrets):
```bash
APPLE_TEAM_ID=ABCDE12345
APPLE_KEY_ID=DEFGHI1234
APPLE_PRIVATE_KEY="-----BEGIN EC PRIVATE KEY-----
...
-----END EC PRIVATE KEY-----"
```

**Important notes for Apple:**
- Apple only returns the user's `name` and `email` on the **first** login. Subsequent logins return only the `sub` claim.
- The platform auto-generates the JWT client secret on-the-fly using your private key.
- Store the private key securely (Infisical/Vault). Never commit it to source control.
- Apple requires the `response_mode=form_post` parameter for web callbacks; the platform handles this automatically.

---

## 4. Register OIDC Configuration in Fabric 4L

### 4.1 Via Infisical Secrets

Store the OIDC configuration in the tenant's Infisical secret path:

| Secret Key | Value | Example |
|------------|-------|---------|
| `OIDC_ISSUER_URL` | IdP issuer URL | `https://auth.example.com/realms/acme` |
| `OIDC_CLIENT_ID` | Application client ID | `fabric4l-acme-prod` |
| `OIDC_CLIENT_SECRET` | Application client secret | (stored encrypted in Infisical) |
| `OIDC_SCOPES` | Space-separated scopes | `openid profile email` |
| `OIDC_REDIRECT_URI` | Callback URL | `https://app.fabric4l.com/api/v1/auth/oidc/callback` |

**Path:** `/tenants/{tenant-id}/oidc/` in the appropriate environment (dev, staging, prod).

### 4.2 Via Tenant Settings API

Alternatively, configure OIDC through the tenant admin API:

```bash
curl -X PATCH https://app.fabric4l.com/api/v1/tenants/{tenant-id}/settings \
  -H "Authorization: Bearer {admin-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "oidc": {
      "enabled": true,
      "issuer_url": "https://auth.example.com/realms/acme",
      "client_id": "fabric4l-acme-prod",
      "client_secret_ref": "vault:oidc/client_secret",
      "scopes": ["openid", "profile", "email"],
      "claim_mapping": {
        "tenant_id_claim": "tenant_id",
        "role_claim": "roles"
      },
      "auto_provision_users": true,
      "default_role": "viewer"
    }
  }'
```

The `OIDCProviderConfig` model (defined in `shared/identity/oidc_config.py`) validates this configuration. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Whether OIDC is active for this tenant |
| `issuer_url` | str | required | IdP issuer URL (must support discovery) |
| `client_id` | str | required | OIDC client ID |
| `client_secret` | str | — | Direct secret value (not recommended for prod) |
| `client_secret_ref` | str | — | Vault/Infisical reference to the secret |
| `auto_provision_users` | bool | `true` | Create user records on first OIDC login |
| `default_role` | str | `viewer` | Role assigned to auto-provisioned users |
| `claim_mapping` | dict | — | Maps IdP claims to Fabric 4L fields |

---

## 5. Authentication Flow

Once configured, the OIDC login flow works as follows:

```
User → GET /auth/oidc/{tenant-slug}/login
       ↓
       Redirect to IdP authorize URL (with PKCE challenge)
       ↓
User authenticates at IdP
       ↓
       Redirect to /auth/oidc/callback?code=...&state=...
       ↓
       Exchange code for tokens (with PKCE verifier)
       ↓
       Verify ID token (signature, issuer, audience, expiry)
       ↓
       Map claims to internal user (auto-provision if enabled)
       ↓
       Issue internal JWT with tenant_id, user_id, roles
       ↓
       Redirect to application with session
```

The implementation lives in `layer4-agents/src/tenants/api/routes/oidc.py`.

---

## 6. Role Mapping

The `map_role_from_claims()` function in `shared/identity/oidc.py` resolves user roles from IdP claims. The mapping priority is:

1. **Custom claim mapping** — If `claim_mapping.role_claim` is set, use that claim's value.
2. **Standard `roles` claim** — Array of role strings from the IdP.
3. **`groups` claim** — Falls back to group membership for role inference.
4. **Default role** — Uses `default_role` from tenant OIDC config if no role claim is found.

### Supported Roles

| Internal Role | Description |
|---------------|-------------|
| `super_admin` | Platform-wide administrator (not assignable via OIDC) |
| `tenant_admin` | Tenant administrator with full tenant access |
| `editor` | Can create and modify resources |
| `viewer` | Read-only access |

---

## 7. Testing OIDC Configuration

### 7.1 Verify Discovery

```bash
curl https://app.fabric4l.com/api/v1/auth/oidc/{tenant-slug}/metadata
```

This returns the resolved OIDC provider metadata, confirming the discovery endpoint is reachable and the configuration is valid.

### 7.2 Test Login Flow

1. Navigate to `https://app.fabric4l.com/api/v1/auth/oidc/{tenant-slug}/login` in a browser.
2. You should be redirected to the IdP's login page.
3. After authenticating, you should be redirected back with a valid session.

### 7.3 Verify Token Claims

After login, inspect the internal JWT to confirm:
- `tenant_id` matches the expected tenant UUID
- `roles` array contains the correct mapped roles
- `sub` matches the IdP user identifier

---

## 8. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "OIDC not configured" error | Missing or disabled OIDC settings | Check tenant settings or Infisical secrets |
| Discovery fails | Issuer URL incorrect or unreachable | Verify `{issuer_url}/.well-known/openid-configuration` is accessible |
| "Invalid ID token" | Clock skew or wrong audience | Check server time sync; verify `client_id` matches IdP |
| No roles assigned | Claim mapping mismatch | Verify `claim_mapping.role_claim` matches your IdP's claim name |
| User not created on login | `auto_provision_users` is false | Enable auto-provisioning or pre-create the user |
| Callback URL mismatch | Redirect URI not registered in IdP | Add the exact callback URL to your IdP's allowed redirects |

---

## 9. Security Considerations

1. **Always use HTTPS** for issuer URLs and callback URLs.
2. **Store client secrets in Infisical**, never in application config or environment variables directly.
3. **Use PKCE** (enabled by default) to protect against authorization code interception.
4. **Rotate client secrets** periodically and update the Infisical path.
5. **Restrict scopes** to the minimum required (`openid profile email`).
6. **Monitor audit logs** for `OIDC_LOGIN` and `OIDC_LOGIN_FAILED` events.

---

## 10. Webhook Integration

External provisioning systems can trigger tenant creation via webhook, which includes OIDC setup:

- **Endpoint:** `POST /api/v1/tenants/{tenant-id}/provisioning/webhook`
- **Authentication:** HMAC-SHA256 signature in `X-Webhook-Signature` header
- **Idempotency:** `X-Webhook-ID` header prevents duplicate processing
- **Reference:** `layer4-agents/src/tenants/api/routes/provisioning.py`

After provisioning completes, configure OIDC via the tenant settings API (Section 4.2).
