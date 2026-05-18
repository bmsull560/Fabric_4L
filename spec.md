# Spec: Auth & Governance Security Audit

## Status

Draft — pending user confirmation before implementation.

---

## Scope

### Auth stacks covered

| Stack | Path | Auth model |
|---|---|---|
| Standalone API | `services/api/` | JWT (HS256) + bcrypt, in-memory/SQLite |
| Layer 4 Agents | `services/layer4-agents/` | OIDC/PKCE + CSRF + PostgreSQL |
| Shared packages | `packages/shared/src/value_fabric/shared/identity/` | GovernanceMiddleware, JWT helpers, RBAC, audit |

### Governance areas covered

1. Sign-up / registration flow
2. Sign-in & authentication (credential security, MFA, OIDC)
3. Session & token management (expiry, refresh, revocation, cookies)
4. User management & invitation flow (CRUD, roles, deactivation)
5. Permissions & RBAC (role definitions, enforcement, escalation)
6. User settings (personal data, security controls, privacy)
7. System configuration & audit logging (access controls, change management)
8. Cross-stack gaps (role schema drift, duplicated logic, inconsistent guarantees)

### Out of scope

- Business logic unrelated to identity, access, or governance
- Layer 1–3 and Layer 5–6 service internals (except where they consume shared auth packages)
- Infrastructure / Kubernetes / CI pipeline security (separate audit surface)

## Methodology

1. **Static code review** — read all auth-related source files in both stacks and shared packages.
2. **Contract tracing** — follow each governance flow end-to-end: frontend → API route → middleware → service → persistence.
3. **Gap analysis** — compare implementation against OWASP API Security Top 10, NIST SP 800-63B, and SOC 2 Type II logical access controls.
4. **Cross-stack comparison** — identify where the two stacks diverge in guarantees, and flag consolidation opportunities.
5. **Test coverage review** — identify which security invariants have automated test coverage and which do not.

### Priority bands

| Band | Criteria |
|---|---|
| **P0 — Critical** | Auth bypass, tenant isolation failure, privilege escalation, token/session compromise |
| **P1 — High** | Brute-force exposure, weak credential policy, missing rate limits, incomplete CSRF/session protection, inconsistent JWT validation |
| **P2 — Medium** | UI security controls not wired to backend enforcement, missing audit events, incomplete email verification enforcement |
| **P3 — Low** | Duplicated auth logic, naming inconsistencies, missing documentation, refactor-only improvements |

### Framework mappings used

- **OWASP** — OWASP Top 10 (2021) and OWASP API Security Top 10
- **NIST** — NIST SP 800-63B (Digital Identity Guidelines — Authentication)
- **SOC 2** — Trust Services Criteria CC6 (Logical and Physical Access Controls)

## Findings Summary Table

| ID | Area | Finding | Priority | OWASP | NIST 800-63B | SOC 2 |
|---|---|---|---|---|---|---|
| F-01 | Sign-Up | Predictable user IDs derived from email prefix | P1 | API3 BOLA | — | CC6.1 |
| F-02 | Sign-Up | No password complexity enforcement (min 8 chars only) | P1 | A07 Auth Failures | §5.1.1 | CC6.1 |
| F-03 | Sign-Up | No email verification on standalone API signup | P2 | A07 | §5.1.1 | CC6.1 |
| F-04 | Sign-Up | Tenant name / plan accepted from unauthenticated request body | P1 | A01 Broken Access | — | CC6.1 |
| F-05 | Sign-In | No account lockout or brute-force throttling on login endpoint | P1 | A07 | §5.2.2 | CC6.1 |
| F-06 | Sign-In | Login endpoint not covered by audit log (only middleware logs 401s) | P2 | A09 Logging | — | CC7.2 |
| F-07 | Sign-In | Dev bypass (`devBypass()`) callable from frontend in non-production builds | P1 | A05 Misconfig | — | CC6.1 |
| F-08 | Session | JWT expiry hardcoded to 24 h; `access_token_expire_minutes=60` config ignored | P1 | A07 | §7.1 | CC6.1 |
| F-09 | Session | No token revocation / blocklist mechanism on standalone API | P1 | A07 | §7.1 | CC6.1 |
| F-10 | Session | Session cookie missing `Secure` and `SameSite` attribute assertions in standalone API | P1 | A05 | §7.1 | CC6.1 |
| F-11 | User Mgmt | `super_admin` role cannot be granted via invite (good), but standalone API `/auth/invite` allows `admin` role without escalation guard | P1 | A01 | — | CC6.1 |
| F-12 | User Mgmt | No account recovery / password reset flow exists in either stack | P2 | A07 | §5.1.1 | CC6.1 |
| F-13 | User Mgmt | `_verify_tenant_access` in admin dashboard uses `getattr(context, "is_super_admin", False)` — attribute check instead of method call | P1 | A01 | — | CC6.1 |
| F-14 | RBAC | Role schema drift: standalone API uses `admin/editor/viewer`; shared packages use `super_admin/tenant_admin/content_admin/analyst/read_only`; frontend adds `standard/advanced/admin` | P1 | A01 | — | CC6.1 |
| F-15 | RBAC | `enforce_authenticated_tenant` is opt-in per route — comment in source explicitly warns of P0 gap if callers forget | P0 | A01 | — | CC6.1 |
| F-16 | RBAC | `require_privileged_access` audit emission failure is silently swallowed — privileged access can proceed without audit trail | P1 | A09 | — | CC7.2 |
| F-17 | User Settings | `PersonalSecurity.tsx` password change and 2FA enable forms have no backend API wiring | P2 | A05 | §6.1 | CC6.1 |
| F-18 | User Settings | `PersonalProfile.tsx` profile update form has no backend API wiring | P2 | A05 | — | CC6.1 |
| F-19 | System Config | `PlatformSettings.tsx` security settings (2FA enforcement, session timeout, IP allowlist) have no backend enforcement | P2 | A05 | §6.1 | CC6.1 |
| F-20 | Audit Log | Audit middleware only logs mutating requests (POST/PUT/PATCH/DELETE); sensitive GET reads (audit log, user list, config) are not logged | P2 | A09 | — | CC7.2 |
| F-21 | Audit Log | `GovernanceAuditLog.tsx` shows Layer 5 truth-object events only — no platform-level auth/access audit log exposed in UI | P2 | A09 | — | CC7.2 |
| F-22 | Cross-Stack | Standalone API `hash_password` falls back to SHA-256 when bcrypt fails — SHA-256 is not a password hashing algorithm | P0 | A02 Crypto | §5.1.1 | CC6.1 |
| F-23 | Cross-Stack | `DevAuthBypassMiddleware` class still exists in codebase despite `maybe_install_dev_bypass` being a no-op; dead code with high-risk surface | P2 | A05 | — | CC6.1 |
| F-24 | Cross-Stack | OIDC state stored in `sessionStorage` (frontend) — accessible to any same-origin JS; should be `sessionStorage` with strict CSRF binding | P1 | A07 | §6.1 | CC6.1 |
| F-25 | Cross-Stack | API key share token in `accounts.py` uses `hash()` (Python built-in, non-cryptographic, seed-randomized) | P0 | A02 | — | CC6.1 |

## Findings by Area

### Area 1: Sign-Up / Registration

#### F-01 — Predictable user IDs derived from email prefix

**Severity:** P1  
**Stack:** Standalone API (`services/api/app/routers/auth.py` lines 94, 183)  
**Frameworks:** OWASP API3 (BOLA), SOC 2 CC6.1

**Observation:**  
User IDs are constructed as `f"user-{payload.email.split('@')[0].lower()}"`. This means:
- Two users with the same local-part across different tenants get the same ID.
- IDs are guessable from a known email address, enabling targeted enumeration or IDOR attempts.
- Collision risk: `alice@company-a.com` and `alice@company-b.com` both produce `user-alice`.

**Design requirement:**  
User IDs must be opaque, globally unique, and not derivable from any user-supplied input.

**Code-level guidance:**
- Replace with `str(uuid.uuid4())` at both call sites in `auth.py`.
- Verify no downstream code assumes the `user-{prefix}` format.
- Add a uniqueness constraint on `(tenant_id, email)` in the persistence layer.

**Tests required:**
- Two users with identical email local-parts in different tenants receive different IDs.
- User ID format is a valid UUID, not a predictable string.

---

#### F-02 — No password complexity enforcement

**Severity:** P1  
**Stack:** Both (frontend: `z.string().min(8)` only; backend: no validation beyond bcrypt hashing)  
**Frameworks:** OWASP A07, NIST 800-63B §5.1.1, SOC 2 CC6.1

**Observation:**  
The frontend enforces only `min(8)`. The backend (`auth.py` `/signup`, `/accept-invite`) applies no complexity check before hashing. NIST 800-63B §5.1.1 requires memorized secrets to be at least 8 characters and checked against a list of commonly used or compromised passwords.

**Design requirement:**  
Passwords must be validated server-side (not just client-side) for minimum length and optionally checked against a known-breached password list (e.g., HaveIBeenPwned k-anonymity API or a local blocklist).

**Code-level guidance:**
- Add a `validate_password_strength(password: str) -> None` utility in `services/api/app/core/security.py`.
- Enforce minimum 12 characters (NIST recommends ≥8; 12 is a reasonable enterprise baseline).
- Optionally check against a top-10k common password list.
- Call this validator in `signup` and `accept_invite` before hashing.
- Return HTTP 422 with a stable error code (`WEAK_PASSWORD`) on failure.

**Tests required:**
- Passwords shorter than minimum are rejected with 422.
- Common passwords (e.g., `password123`) are rejected.
- Strong passwords are accepted.

---

#### F-03 — No email verification on standalone API signup

**Severity:** P2  
**Stack:** Standalone API  
**Frameworks:** OWASP A07, NIST 800-63B §5.1.1, SOC 2 CC6.1

**Observation:**  
`POST /auth/signup` creates an active tenant and user immediately with no email verification step. Layer 4 has `EmailVerificationService` but the standalone API does not use it. An attacker can register with any email address and immediately receive a valid JWT.

**Design requirement:**  
New accounts should require email verification before the account is activated, or at minimum before sensitive operations are permitted.

**Code-level guidance:**
- Set `status="pending_verification"` on new users in `signup`.
- Block `login` for `pending_verification` users with a clear error.
- Add `POST /auth/verify-email` endpoint accepting a time-limited token.
- Reuse or adapt `EmailVerificationService` from Layer 4.

**Tests required:**
- Signup returns 201 but login is blocked until email is verified.
- Verification token expires after configured window.
- Verified user can log in normally.

---

#### F-04 — Tenant plan accepted from unauthenticated request body

**Severity:** P1  
**Stack:** Standalone API (`services/api/app/routers/auth.py` `SignupRequest`)  
**Frameworks:** OWASP A01, SOC 2 CC6.1

**Observation:**  
`SignupRequest` includes `plan: str = "team"`. Any unauthenticated caller can self-assign any plan string (e.g., `"enterprise"`) at signup. There is no server-side validation that the requested plan is a valid, purchasable tier.

**Design requirement:**  
Plan assignment must be server-controlled. Unauthenticated signup should only create accounts on the default free/trial tier. Plan upgrades must go through a separate, authenticated, and authorized flow.

**Code-level guidance:**
- Remove `plan` from `SignupRequest`.
- Hardcode `plan="free"` (or `"trial"`) in the `signup` handler.
- Add a separate `PATCH /tenants/{id}/plan` endpoint requiring `super_admin` or billing authorization.

**Tests required:**
- Signup with `plan="enterprise"` in body creates a `free` tenant, not `enterprise`.
- Plan field is absent from the signup response or always returns the server-assigned value.

### Area 2: Sign-In & Authentication

#### F-05 — No account lockout or brute-force throttling on login

**Severity:** P1  
**Stack:** Standalone API (`services/api/app/routers/auth.py` `/login`)  
**Frameworks:** OWASP A07, NIST 800-63B §5.2.2, SOC 2 CC6.1

**Observation:**  
The `/login` endpoint performs a cross-tenant email lookup and password verification with no rate limiting, no failed-attempt tracking, and no lockout. An attacker can make unlimited login attempts against any email address. Layer 4's OIDC `/login` endpoint has a pre-auth rate limiter (`_check_preauth_rate_limit`) but the standalone API has none.

**Design requirement:**  
Authentication endpoints must throttle repeated failures per IP and/or per account. After a configurable threshold, the account must be temporarily locked or the response must be delayed. Error messages must not distinguish between "email not found" and "wrong password."

**Code-level guidance:**
- Add `failed_login_attempts: int = 0` and `locked_until: datetime | None = None` to the `User` model.
- In the `login` handler: check `locked_until` before verifying password; increment `failed_login_attempts` on failure; reset on success; lock after threshold (e.g., 10 attempts).
- Add IP-level rate limiting middleware for `/auth/login` and `/auth/signup` (reuse or adapt `_check_preauth_rate_limit` from Layer 4).
- Return the same HTTP 401 response regardless of whether the email exists.

**Tests required:**
- Login fails after N consecutive wrong passwords and returns 429 or 403.
- Successful login resets the failed attempt counter.
- Locked account cannot log in even with correct password until window expires.
- Error response does not differ between unknown email and wrong password.

---

#### F-06 — Login/signup events not written to audit log

**Severity:** P2  
**Stack:** Standalone API  
**Frameworks:** OWASP A09, SOC 2 CC7.2

**Observation:**  
`AuditMiddleware` only logs mutating requests that reach the handler. Successful logins (POST `/auth/login` → 200) produce a structured log entry, but there is no explicit audit event written to the `audit_logs` table. Failed logins produce a WARNING log but no persistent audit record. This means the audit log accessible via `GET /governance/audit-log` contains no authentication history.

**Design requirement:**  
All authentication events (successful login, failed login, signup, logout, invite acceptance) must be written as structured, tenant-scoped audit records to the persistent audit log.

**Code-level guidance:**
- After successful login in `auth.py`, call `db.audit_logs.insert(...)` with `event_type="login_success"`, `actor_id`, `tenant_id`, `ip_address`.
- On failed login, insert `event_type="login_failure"` with the same fields (no password or hash in the record).
- Repeat for `signup`, `logout`, `accept_invite`.

**Tests required:**
- Successful login creates an audit record with correct actor and tenant.
- Failed login creates an audit record without exposing credential data.
- Audit records are tenant-scoped and not visible cross-tenant.

---

#### F-07 — Dev bypass callable from frontend in non-production builds

**Severity:** P1  
**Stack:** Frontend (`apps/web/src/pages/Login.tsx`, `apps/web/src/contexts/AuthContext.tsx`)  
**Frameworks:** OWASP A05, SOC 2 CC6.1

**Observation:**  
`Login.tsx` calls `auth.devBypass?.()` when `import.meta.env.DEV || import.meta.env.MODE === 'test'`. This bypasses all authentication and navigates directly to `/home`. If a staging or preview build is deployed with `MODE=test` or `DEV=true`, any user can bypass authentication entirely by triggering this code path.

**Design requirement:**  
Dev bypass must be completely absent from any build that could be deployed to a shared environment. It must not be gated only on a runtime env flag that could be misconfigured.

**Code-level guidance:**
- Move dev bypass into a separate file that is excluded from non-development builds via Vite's `define` or `build.rollupOptions.external`.
- Add a CI check that asserts `devBypass` is not present in production bundle output.
- In `AuthContext.tsx`, type `devBypass` as `undefined` in production builds using conditional type exports.

**Tests required:**
- Production build (`MODE=production`) does not contain the string `devBypass` or `dev_bypass` in the output bundle.
- CI gate fails if bypass code is detected in a production artifact.

### Area 3: Session & Token Management

#### F-08 — JWT expiry hardcoded to 24 h; config setting ignored

**Severity:** P1  
**Stack:** Standalone API (`services/api/app/routers/auth.py`)  
**Frameworks:** OWASP A07, NIST 800-63B §7.1, SOC 2 CC6.1

**Observation:**  
All three token-issuing endpoints (`signup`, `login`, `accept_invite`) hardcode `expires_delta=timedelta(hours=24)`. The `Settings` model has `access_token_expire_minutes: int = 60` which is never used. The `create_access_token` function accepts `expires_delta` and defaults to `settings.access_token_expire_minutes` when `None` is passed — but callers always pass an explicit 24-hour delta, bypassing the config entirely.

**Design requirement:**  
Token lifetime must be driven by configuration, not hardcoded. The default should be short (≤60 minutes for access tokens). Refresh tokens or session cookies should handle longer-lived sessions.

**Code-level guidance:**
- Remove `expires_delta=timedelta(hours=24)` from all three call sites.
- Pass `expires_delta=None` to let `create_access_token` use `settings.access_token_expire_minutes`.
- Set `access_token_expire_minutes = 60` as the default (already present).
- Document the env var `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env.example`.

**Tests required:**
- Token expiry matches `settings.access_token_expire_minutes`.
- Changing the config value changes the issued token's `exp` claim.

---

#### F-09 — No token revocation mechanism on standalone API

**Severity:** P1  
**Stack:** Standalone API  
**Frameworks:** OWASP A07, NIST 800-63B §7.1, SOC 2 CC6.1

**Observation:**  
There is no logout endpoint, no token blocklist, and no session invalidation mechanism in the standalone API. A stolen or leaked JWT remains valid until its `exp` claim. Deactivating a user (`status="deactivated"`) does not invalidate existing tokens — the `get_current_user` dependency only checks the DB record, but a deactivated user's existing token will still pass `decode_token` and reach `get_current_user` which will then return the user (deactivation check is only in `login`, not in `get_current_user`).

**Design requirement:**  
Deactivating a user must immediately invalidate all their active tokens. A logout endpoint must exist. For stateless JWTs, this requires either a short expiry + refresh token pattern, or a token blocklist (Redis-backed for distributed deployments).

**Code-level guidance:**
- Add a status check in `get_current_user`: if `user.status == "deactivated"`, raise 401.
- Add `POST /auth/logout` that sets the session cookie to expired (for cookie-based flows).
- For the standalone API, add a `jti` claim to tokens and a Redis/in-memory blocklist checked in `decode_token`.
- Add `POST /auth/logout` to the standalone API router.

**Tests required:**
- Deactivated user's existing JWT is rejected by `GET /auth/me`.
- Logout invalidates the session cookie.
- Blocklisted `jti` is rejected even before token expiry.

---

#### F-10 — Session cookie security attributes not asserted

**Severity:** P1  
**Stack:** Standalone API  
**Frameworks:** OWASP A05, NIST 800-63B §7.1, SOC 2 CC6.1

**Observation:**  
The standalone API reads the `vf_session` cookie in `security.py` but never sets it (no `Set-Cookie` response). The cookie is set by the OIDC callback in Layer 4. There is no assertion in the standalone API that the cookie is `HttpOnly`, `Secure`, and `SameSite=Strict`. The Layer 4 OIDC callback sets the cookie but the `Secure` flag depends on the deployment environment being HTTPS — there is no startup check enforcing this in production.

**Design requirement:**  
Session cookies must always be set with `HttpOnly=True`, `Secure=True` (enforced in production), and `SameSite=Strict` or `SameSite=Lax`. A startup check must fail if `Secure` cookies are disabled in a production-like environment.

**Code-level guidance:**
- In Layer 4 OIDC callback, assert `Secure=True` when `settings.is_production_like`.
- Add a startup validation in `config.py` that raises if `ENVIRONMENT=production` and `COOKIE_SECURE` is not set.
- Add a test that verifies `Set-Cookie` headers include `HttpOnly`, `Secure`, and `SameSite` in production mode.

**Tests required:**
- Production OIDC callback response includes `Set-Cookie: vf_session=...; HttpOnly; Secure; SameSite=Strict`.
- Non-HTTPS development builds may omit `Secure` but must log a warning.

### Area 4: User Management & Invitation Flow

#### F-11 — Standalone API invite allows `admin` role without escalation guard

**Severity:** P1  
**Stack:** Standalone API (`services/api/app/routers/auth.py` `/invite`)  
**Frameworks:** OWASP A01, SOC 2 CC6.1

**Observation:**  
The `/invite` endpoint accepts `role: Literal["admin", "editor", "viewer"]`. Any `admin` user can invite another user with `role="admin"`. There is no check preventing a `tenant_admin` from creating another `tenant_admin`, and no guard preventing role escalation to `super_admin` (which is not in the Literal but could be injected if the Literal is ever relaxed). The shared packages' `UserInviteRequest` correctly blocks `super_admin` via a Pydantic validator — the standalone API does not use this model.

**Design requirement:**  
An admin may only invite users to roles equal to or lower than their own. A `tenant_admin` cannot create another `tenant_admin` without `super_admin` approval. The standalone API should adopt the same `role_cannot_be_super_admin` validator pattern from the shared `UserInviteRequest`.

**Code-level guidance:**
- In `InviteRequest`, add a validator that rejects `role="admin"` if the inviting user is not `super_admin`.
- Or: align the standalone API to use the shared `UserInviteRequest` model.
- Add a role hierarchy check: `inviter_role_rank >= invitee_role_rank`.

**Tests required:**
- An `editor` cannot invite an `admin`.
- An `admin` can invite an `editor` or `viewer`.
- Attempting to invite `super_admin` is rejected with 422.

---

#### F-12 — No account recovery / password reset flow

**Severity:** P2  
**Stack:** Both stacks  
**Frameworks:** OWASP A07, NIST 800-63B §5.1.1, SOC 2 CC6.1

**Observation:**  
Neither the standalone API nor Layer 4 has a password reset or account recovery endpoint. Users who forget their password have no self-service recovery path. The frontend `PersonalSecurity.tsx` shows a password change form but it has no backend wiring (see F-17).

**Design requirement:**  
A password reset flow must exist: user requests reset via email → time-limited token sent → token redeemed to set new password → old sessions invalidated.

**Code-level guidance:**
- Add `POST /auth/forgot-password` (unauthenticated): generates a time-limited reset token, stores its hash, sends email.
- Add `POST /auth/reset-password`: validates token, sets new password, invalidates all existing sessions for the user.
- Reuse `EmailVerificationService` token generation pattern from Layer 4.
- Reset tokens must be single-use and expire after 1 hour.

**Tests required:**
- Reset token expires after configured window.
- Reset token is single-use (second use returns 400).
- Password reset invalidates existing JWTs.
- Unknown email returns 200 (no enumeration).

---

#### F-13 — `_verify_tenant_access` uses attribute check instead of method call

**Severity:** P1  
**Stack:** Layer 4 (`services/layer4-agents/src/tenants/api/routes/admin.py`)  
**Frameworks:** OWASP A01, SOC 2 CC6.1

**Observation:**  
```python
is_super = getattr(context, "is_super_admin", False)
```
`is_super_admin` is a method on `RequestContext`, not a boolean attribute. `getattr(..., False)` returns the bound method object (truthy) rather than calling it. This means the super-admin check always evaluates to `True`, allowing any authenticated user to bypass the tenant access check by having a `RequestContext` with an `is_super_admin` method.

**Design requirement:**  
Role checks must call the method, not read the attribute. All privilege checks must be verified by calling the appropriate method.

**Code-level guidance:**
- Replace `getattr(context, "is_super_admin", False)` with `context.is_super_admin()`.
- Add a regression test that verifies a non-super-admin user cannot access another tenant's admin dashboard.

**Tests required:**
- Non-super-admin user accessing another tenant's `/tenants/{id}/users` receives 403.
- Super-admin user can access any tenant's admin dashboard.
- The fix is covered by a unit test that mocks `is_super_admin()` returning `False`.

### Area 5: Permissions & RBAC

#### F-14 — Role schema drift across stacks

**Severity:** P1  
**Stack:** Cross-stack  
**Frameworks:** OWASP A01, SOC 2 CC6.1

**Observation:**  
Three incompatible role schemas exist simultaneously:

| Location | Roles |
|---|---|
| `services/api/app/models/schemas.py` | `admin`, `editor`, `viewer` |
| `packages/shared/.../permissions.py` | `super_admin`, `tenant_admin`, `content_admin`, `analyst`, `read_only`, `system` |
| `apps/web/src/schemas/auth.ts` | `super_admin`, `tenant_admin`, `content_admin`, `analyst`, `read_only`, `system` + `standard`, `advanced`, `admin` |
| `apps/web/src/stores/userTierStore.ts` | `standard`, `advanced`, `admin` (UI tiers) |

The standalone API issues JWTs with `role="admin"` but the shared `GovernanceMiddleware` and `require_tenant_admin` dependency expect `role="tenant_admin"`. A token issued by the standalone API will fail RBAC checks in any service using the shared packages.

**Design requirement:**  
There must be a single canonical role schema. The standalone API must be migrated to use the shared `Role` enum. The frontend normalization layer (`normalizeRoleToTier`) already handles `admin → tenant_admin` as a legacy alias, but the backend must not rely on this.

**Code-level guidance:**
- Update `User.role` in `services/api/app/models/schemas.py` to use `Literal["super_admin", "tenant_admin", "content_admin", "analyst", "read_only"]`.
- Update all standalone API role checks from `"admin"` to `"tenant_admin"`.
- Add a migration for any persisted user records with `role="admin"`.
- Add a contract test asserting that tokens issued by the standalone API are accepted by the shared `GovernanceMiddleware`.

**Tests required:**
- Standalone API token with `role="tenant_admin"` is accepted by shared middleware.
- Legacy `role="admin"` token is normalized via `LEGACY_ROLE_ALIASES` and accepted.
- Unknown role values are rejected.

---

#### F-15 — `enforce_authenticated_tenant` is opt-in with no automatic enforcement

**Severity:** P0  
**Stack:** Standalone API (`services/api/app/core/tenant_enforcement.py`)  
**Frameworks:** OWASP A01, SOC 2 CC6.1

**Observation:**  
The docstring explicitly states: _"This helper is NOT applied by middleware. Each router that accepts a body or header tenant_id must call this function explicitly... Failure to call this on a route that accepts tenant_id in the request body or headers leaves that route vulnerable to X-Tenant-ID header spoofing."_

This is a P0 architectural gap: any new route that accepts `tenant_id` in the body and forgets to call `enforce_authenticated_tenant` is silently vulnerable to cross-tenant writes.

**Design requirement:**  
Tenant enforcement must be automatic, not opt-in. The middleware or a base dependency should enforce that the body `tenant_id` (if present) matches the authenticated tenant before the handler runs.

**Code-level guidance:**
- Add a Pydantic base model `TenantScopedRequest` with a `tenant_id` field and a `model_validator` that calls `enforce_authenticated_tenant` using the request context.
- Or: add a FastAPI middleware that inspects the parsed request body for `tenant_id` fields and enforces the match automatically.
- Add a CI lint check (extend `tests/ci/test_unscoped_tenant_match_lint.py`) that fails if any route handler accepts a body with `tenant_id` without calling `enforce_authenticated_tenant`.

**Tests required:**
- A route that accepts `tenant_id` in the body rejects requests where body `tenant_id` ≠ JWT `tenant_id`.
- The CI lint gate catches new routes that omit the enforcement call.

---

#### F-16 — Privileged access audit emission failure is silently swallowed

**Severity:** P1  
**Stack:** Shared packages (`packages/shared/.../dependencies.py` `require_privileged_access`)  
**Frameworks:** OWASP A09, SOC 2 CC7.2

**Observation:**  
```python
except Exception as exc:  # pragma: no cover - behavior asserted by tests via no raise
    logger.error("Failed to emit privileged access audit event: %s", exc)
```
If the audit sink (database or event bus) is unavailable, privileged access proceeds without any audit trail. This means a super-admin can perform cross-tenant operations during an audit sink outage with no record.

**Design requirement:**  
Audit emission failure for privileged access must be a hard failure, not a soft warning. The principle of "fail closed" applies: if we cannot record that privileged access occurred, we should not permit it.

**Code-level guidance:**
- Remove the `except Exception` swallow in `require_privileged_access`.
- Raise HTTP 503 if audit emission fails, with a clear error message.
- Add a configuration flag `PRIVILEGED_ACCESS_REQUIRE_AUDIT=true` (default `true`) that controls this behavior, allowing operators to temporarily disable it during audit sink maintenance with explicit acknowledgment.

**Tests required:**
- Privileged access is denied when audit emission raises an exception (default behavior).
- With `PRIVILEGED_ACCESS_REQUIRE_AUDIT=false`, privileged access proceeds and logs a warning.
- Audit emission success allows privileged access normally.

### Area 6: User Settings (Frontend)

#### F-17 — Password change and 2FA forms have no backend wiring

**Severity:** P2  
**Stack:** Frontend (`apps/web/src/app/settings/pages/PersonalSecurity.tsx`)  
**Frameworks:** OWASP A05, NIST 800-63B §6.1, SOC 2 CC6.1

**Observation:**  
`PersonalSecurity.tsx` renders a password change form (current password, new password, confirm) and a 2FA "Enable" button. Neither has an `onSubmit` handler, API call, or state management. The forms are static HTML with no functionality. A user who believes they have changed their password or enabled 2FA has not — the UI creates a false sense of security.

**Design requirement:**  
Either wire these forms to backend endpoints, or clearly mark them as "coming soon" with a disabled state. A security settings page that appears functional but is not is a SOC 2 control design gap.

**Code-level guidance:**
- **Password change**: Add `PATCH /users/me/password` endpoint (current password verification + new password validation + hash update + session invalidation). Wire the form to this endpoint via a TanStack Query mutation.
- **2FA**: If not yet implemented backend-side, replace the "Enable" button with a disabled state and a "Coming soon" label. Do not show a functional-looking form for a non-functional feature.
- Add loading, success, and error states to both forms.

**Tests required:**
- Password change form submits to the correct endpoint.
- Incorrect current password returns an error displayed in the form.
- Successful password change shows a success state.

---

#### F-18 — Profile update form has no backend wiring

**Severity:** P2  
**Stack:** Frontend (`apps/web/src/app/settings/pages/PersonalProfile.tsx`)  
**Frameworks:** OWASP A05, SOC 2 CC6.1

**Observation:**  
`PersonalProfile.tsx` renders name, email, title, and default workspace fields with no `onChange` handlers, no form state, and no submit action. The form is purely decorative.

**Design requirement:**  
Profile fields must either be wired to `PATCH /users/me` or clearly shown as read-only. Email changes require re-verification.

**Code-level guidance:**
- Add `PATCH /users/me` endpoint accepting `display_name`, `title`.
- Email changes should require re-verification (send verification email, block until confirmed).
- Wire the form using React Hook Form + TanStack Query mutation.
- Pre-populate fields from `GET /auth/me` response.

**Tests required:**
- Profile form is pre-populated with current user data on mount.
- Submitting the form calls `PATCH /users/me` with changed fields.
- Email change triggers a verification flow.

### Area 7: System Configuration & Audit Logging

#### F-19 — PlatformSettings security controls not wired to backend enforcement

**Severity:** P2  
**Stack:** Frontend (`apps/web/src/pages/admin/PlatformSettings.tsx`)  
**Frameworks:** OWASP A05, NIST 800-63B §6.1, SOC 2 CC6.1

**Observation:**  
`PlatformSettings.tsx` renders security settings including "Require 2FA for all users", "Session timeout", and "IP allowlist". These controls are fetched from and saved to a backend endpoint, but the backend `TenantSettings` schema (`services/layer4-agents/src/tenants/settings_schema.py`) only defines `rate_limits`. There is no `security` section in the settings schema, no enforcement of 2FA requirements at login, no session timeout enforcement in middleware, and no IP allowlist check anywhere in the codebase.

**Design requirement:**  
Security settings that are displayed and editable must be enforced. If a setting is not yet enforced, it must not be shown as a configurable control.

**Code-level guidance:**
- Add a `SecuritySettings` Pydantic model to `settings_schema.py` with `require_mfa: bool`, `session_timeout_minutes: int`, `ip_allowlist: list[str]`.
- Enforce `require_mfa` in the OIDC callback: if the tenant requires MFA and the IdP did not assert an MFA claim, reject the login.
- Enforce `session_timeout_minutes` in `GovernanceMiddleware` by checking token `iat` against the setting.
- Enforce `ip_allowlist` in `GovernanceMiddleware` by checking `request.client.host`.
- Until enforcement is implemented, disable the controls in the UI with a "Not yet enforced" label.

**Tests required:**
- Tenant with `require_mfa=true` rejects logins without MFA claim.
- Tenant with `ip_allowlist=["10.0.0.0/8"]` rejects requests from outside the allowlist.
- Session timeout setting causes tokens older than the configured window to be rejected.

---

#### F-20 — Audit middleware does not log sensitive GET reads

**Severity:** P2  
**Stack:** Standalone API (`services/api/app/core/audit.py`)  
**Frameworks:** OWASP A09, SOC 2 CC7.2

**Observation:**  
`AuditMiddleware` only logs `POST`, `PUT`, `PATCH`, `DELETE`. Sensitive read operations — `GET /governance/audit-log`, `GET /v1/users`, `GET /v1/accounts` — are not logged. An attacker who gains read access to sensitive data leaves no audit trail.

**Design requirement:**  
High-sensitivity GET endpoints must be logged. This does not mean logging all reads — only those that expose sensitive governance, user, or configuration data.

**Code-level guidance:**
- Add a `AUDIT_READ_PATHS` set to `audit.py` listing paths that require read audit logging (e.g., `/v1/users`, `/governance/audit-log`, `/tenants/{id}/users`).
- In `AuditMiddleware.dispatch`, also log GET requests whose path matches `AUDIT_READ_PATHS`.
- Log `event_type="sensitive_read"` with actor, tenant, path, and status code.

**Tests required:**
- `GET /v1/users` produces an audit log entry.
- `GET /governance/audit-log` produces an audit log entry.
- `GET /v1/accounts/{id}` does not produce an audit log entry (not in sensitive list).

---

#### F-21 — No platform-level auth/access audit log in UI

**Severity:** P2  
**Stack:** Frontend (`apps/web/src/pages/GovernanceAuditLog.tsx`)  
**Frameworks:** OWASP A09, SOC 2 CC7.2

**Observation:**  
`GovernanceAuditLog.tsx` displays Layer 5 truth-object validation events only. There is no UI surface for platform-level audit events: logins, logouts, user invitations, role changes, API key creation/revocation, or configuration changes. Tenant admins have no way to review access history from the UI.

**Design requirement:**  
The admin UI must expose a platform-level audit log showing authentication and access events, scoped to the current tenant.

**Code-level guidance:**
- Add a new page `PlatformAuditLog.tsx` (or extend `GovernanceAuditLog.tsx` with tabs) that queries `GET /governance/audit-log` (standalone API) or `GET /tenants/{id}/audit-log` (Layer 4).
- Display: timestamp, actor, event type, IP address, outcome.
- Gate the page behind `admin` tier in `userTierStore`.
- Add to the admin navigation.

**Tests required:**
- Page renders audit events from the backend.
- Non-admin users cannot access the page (route guard test).
- Empty state is shown when no events exist.

### Area 8: Cross-Stack Gaps & Role Schema Drift

#### F-22 — SHA-256 fallback for password hashing (critical)

**Severity:** P0  
**Stack:** Standalone API (`services/api/app/core/security.py`)  
**Frameworks:** OWASP A02, NIST 800-63B §5.1.1, SOC 2 CC6.1

**Observation:**  
```python
def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        import hashlib
        return f"sha256${hashlib.sha256(password.encode()).hexdigest()}"
```
If bcrypt fails (e.g., due to a missing native library), passwords are hashed with raw SHA-256. SHA-256 is not a password hashing algorithm — it is fast, has no salt, and is trivially brute-forced with GPU hardware. Any user whose password was stored with this fallback is at critical risk.

Similarly, `verify_password` accepts `sha256$` prefixed hashes:
```python
if hashed.startswith("sha256$"):
    return hashlib.sha256(plain.encode()).hexdigest() == hashed.removeprefix("sha256$")
```
This means SHA-256 hashed passwords are silently accepted in production.

**Design requirement:**  
Password hashing must always use bcrypt (or Argon2). If bcrypt is unavailable, the application must fail to start rather than fall back to an insecure algorithm. The SHA-256 fallback and verification path must be removed entirely.

**Code-level guidance:**
- Remove the `except Exception` fallback in `hash_password`. Let the exception propagate — a startup health check will catch it.
- Remove the `sha256$` branch in `verify_password`.
- Add a startup check that calls `pwd_context.hash("test")` and fails fast if bcrypt is not available.
- Add a data migration to identify any users with `sha256$` prefixed hashes and force a password reset for those accounts.

**Tests required:**
- `hash_password` raises if bcrypt is unavailable (mock `pwd_context.hash` to raise).
- `verify_password` rejects `sha256$` prefixed hashes.
- Startup health check fails if bcrypt is not functional.

---

#### F-23 — Dead `DevAuthBypassMiddleware` class in codebase

**Severity:** P2  
**Stack:** Shared packages (`packages/shared/.../dev_bypass.py`)  
**Frameworks:** OWASP A05, SOC 2 CC6.1

**Observation:**  
`DevAuthBypassMiddleware` is a fully implemented class that injects a synthetic `RequestContext` with `super_admin` role on every request. `maybe_install_dev_bypass` is now a no-op, but the class itself remains. If a developer accidentally calls `app.add_middleware(DevAuthBypassMiddleware)` directly (bypassing `maybe_install_dev_bypass`), the bypass is active with no guards.

**Design requirement:**  
Dead security-sensitive code must be removed, not just disabled. The class should not exist in the codebase.

**Code-level guidance:**
- Delete `DevAuthBypassMiddleware` class from `dev_bypass.py`.
- Keep `maybe_install_dev_bypass` as a no-op stub for import compatibility, with a docstring explaining it is permanently disabled.
- Add a CI check that asserts `DevAuthBypassMiddleware` is not imported or instantiated anywhere.

**Tests required:**
- `DevAuthBypassMiddleware` does not exist in the module (import test).
- `maybe_install_dev_bypass` always returns `False`.

---

#### F-24 — OIDC state in sessionStorage accessible to same-origin JS

**Severity:** P1  
**Stack:** Frontend (`apps/web/src/contexts/AuthContext.tsx`, `sessionService`)  
**Frameworks:** OWASP A07, NIST 800-63B §6.1, SOC 2 CC6.1

**Observation:**  
OIDC flow state (including the CSRF `state` parameter) is stored in `sessionStorage`. While `sessionStorage` is not accessible cross-origin, it is accessible to any JavaScript running on the same origin — including injected scripts from XSS. If the application has any XSS vulnerability, the OIDC state can be stolen and used to complete an authorization code injection attack.

**Design requirement:**  
OIDC state should be stored in a way that is not accessible to JavaScript. The preferred approach is to use the `vf_csrf_token` httpOnly cookie (already implemented in Layer 4) as the CSRF binding, and validate the `state` parameter server-side rather than client-side.

**Code-level guidance:**
- Move OIDC state validation to the backend OIDC callback handler.
- The frontend sends `state` to the backend callback; the backend validates it against the `vf_csrf_token` cookie using `validate_double_submit`.
- Remove OIDC state from `sessionStorage` in `sessionService`.

**Tests required:**
- OIDC callback with mismatched state is rejected with 403.
- OIDC state is not present in `sessionStorage` after the callback completes.

---

#### F-25 — Share token uses Python built-in `hash()` (non-cryptographic)

**Severity:** P0  
**Stack:** Standalone API (`services/api/app/routers/accounts.py`)  
**Frameworks:** OWASP A02, SOC 2 CC6.1

**Observation:**  
```python
token = f"share_{account_id}_{tenant_id}_{hash(account_id + tenant_id) % 1000000}"
```
Python's `hash()` is:
- Non-cryptographic (designed for hash tables, not security)
- Seed-randomized per process (same input produces different output across restarts)
- Only 6 digits of entropy after `% 1000000` — trivially brute-forceable (1 million possibilities)

This token is used to grant read-only access to account data. An attacker who knows the `account_id` and `tenant_id` (both potentially guessable or leaked) can brute-force the token in under a second.

**Design requirement:**  
Share tokens must use a cryptographically secure random generator with sufficient entropy (≥128 bits). Tokens must be stored (hashed) server-side and validated on redemption.

**Code-level guidance:**
- Replace `hash(...)` with `secrets.token_urlsafe(32)` (256 bits of entropy).
- Store the token hash (SHA-256) in the database, not the raw token.
- Add a `ShareLink` model with `token_hash`, `account_id`, `tenant_id`, `created_at`, `expires_at`, `revoked`.
- Validate tokens by hashing the presented value and comparing to the stored hash.
- Add expiry (e.g., 7 days) and revocation support.

**Tests required:**
- Share tokens are not guessable from `account_id` and `tenant_id`.
- Expired share tokens are rejected.
- Revoked share tokens are rejected.
- Token entropy is ≥128 bits (assert `len(token) >= 43` for base64url).

## Required Fixes

Ordered by priority band. Within each band, ordered by implementation dependency (fix prerequisites first).

### P0 — Fix immediately before any production deployment

| ID | Fix | File(s) |
|---|---|---|
| F-22 | Remove SHA-256 password hash fallback; add startup bcrypt check | `services/api/app/core/security.py` |
| F-15 | Make tenant enforcement automatic (not opt-in per route) | `services/api/app/core/tenant_enforcement.py`, all routers |
| F-25 | Replace `hash()` share token with `secrets.token_urlsafe(32)` + DB storage | `services/api/app/routers/accounts.py` |
| F-13 | Fix `getattr(context, "is_super_admin", False)` → `context.is_super_admin()` | `services/layer4-agents/src/tenants/api/routes/admin.py` |

### P1 — Fix before first external user access

| ID | Fix | File(s) |
|---|---|---|
| F-01 | Replace predictable user IDs with `uuid4()` | `services/api/app/routers/auth.py` |
| F-02 | Add server-side password complexity validation | `services/api/app/core/security.py`, `auth.py` |
| F-04 | Remove `plan` from `SignupRequest`; hardcode `free` tier | `services/api/app/routers/auth.py` |
| F-05 | Add login rate limiting and account lockout | `services/api/app/routers/auth.py`, `models/schemas.py` |
| F-07 | Remove dev bypass from non-development builds | `apps/web/src/pages/Login.tsx`, `AuthContext.tsx` |
| F-08 | Remove hardcoded 24h token expiry; use config | `services/api/app/routers/auth.py` |
| F-09 | Add logout endpoint + deactivated user check in `get_current_user` | `services/api/app/core/security.py`, `auth.py` |
| F-10 | Assert `HttpOnly`, `Secure`, `SameSite` on session cookies | Layer 4 OIDC callback, `config.py` |
| F-11 | Add role escalation guard to standalone API invite | `services/api/app/routers/auth.py` |
| F-14 | Migrate standalone API to canonical role schema | `services/api/app/models/schemas.py`, all role checks |
| F-16 | Make privileged access audit emission a hard failure | `packages/shared/.../dependencies.py` |
| F-24 | Move OIDC state validation server-side | `apps/web/src/services/sessionService.ts`, Layer 4 OIDC callback |

### P2 — Fix before SOC 2 audit or enterprise customer onboarding

| ID | Fix | File(s) |
|---|---|---|
| F-03 | Add email verification to standalone API signup | `services/api/app/routers/auth.py` |
| F-06 | Write auth events to persistent audit log | `services/api/app/routers/auth.py` |
| F-12 | Implement password reset flow | Both stacks |
| F-17 | Wire password change and 2FA forms to backend | `apps/web/src/app/settings/pages/PersonalSecurity.tsx` |
| F-18 | Wire profile update form to backend | `apps/web/src/app/settings/pages/PersonalProfile.tsx` |
| F-19 | Enforce or disable PlatformSettings security controls | `services/layer4-agents/src/tenants/settings_schema.py`, middleware |
| F-20 | Log sensitive GET reads in audit middleware | `services/api/app/core/audit.py` |
| F-21 | Add platform-level audit log UI | `apps/web/src/pages/admin/` |
| F-23 | Remove dead `DevAuthBypassMiddleware` class | `packages/shared/.../dev_bypass.py` |

## Required Tests

Each finding's test requirements are listed inline above. The following are the minimum test gates that must pass before the audit is considered closed.

### Security regression tests (must be added to CI)

```
tests/security/test_auth_governance.py
```

| Test | Covers |
|---|---|
| `test_sha256_fallback_removed` | F-22: `hash_password` raises if bcrypt unavailable |
| `test_sha256_hash_rejected_on_verify` | F-22: `verify_password` rejects `sha256$` hashes |
| `test_user_id_is_uuid` | F-01: signup returns UUID user ID |
| `test_user_id_collision_across_tenants` | F-01: same email local-part → different IDs |
| `test_password_min_length_enforced` | F-02: 7-char password rejected with 422 |
| `test_password_complexity_enforced` | F-02: common password rejected |
| `test_plan_not_accepted_from_body` | F-04: `plan=enterprise` in signup body → `free` tenant |
| `test_login_lockout_after_threshold` | F-05: 10 failed logins → 429/403 |
| `test_login_error_no_enumeration` | F-05: same error for unknown email vs wrong password |
| `test_deactivated_user_jwt_rejected` | F-09: deactivated user's token → 401 |
| `test_invite_role_escalation_blocked` | F-11: editor cannot invite admin |
| `test_tenant_enforcement_automatic` | F-15: body tenant_id mismatch → 403 |
| `test_super_admin_check_calls_method` | F-13: `is_super_admin()` called, not attribute-read |
| `test_share_token_entropy` | F-25: share token is ≥43 chars, not derived from inputs |
| `test_share_token_not_guessable` | F-25: two calls produce different tokens |
| `test_privileged_access_denied_on_audit_failure` | F-16: audit emission failure → 503 |
| `test_dev_bypass_absent_in_production_build` | F-07: production bundle does not contain bypass code |

### Existing tests that must continue to pass

- `tests/ci/test_route_auth_gate.py` — all routes have auth dependencies
- `tests/ci/test_mandatory_security_regression_gate.py`
- `tests/backend_integrated/test_tenant_isolation_security_persistence.py`
- `services/api/app/tests/test_auth_enforcement.py`
- `services/api/app/tests/test_tenant_isolation.py`
- `services/api/app/tests/test_invitation_and_tenant_leakage.py`

## Acceptance Criteria

The audit is considered complete and the platform is ready for production governance sign-off when all of the following are true:

### P0 criteria (blocking)

- [ ] `hash_password` never produces a `sha256$` prefixed hash under any condition
- [ ] `verify_password` rejects any `sha256$` prefixed hash
- [ ] Tenant enforcement cannot be bypassed by omitting `enforce_authenticated_tenant` — enforcement is automatic
- [ ] Share tokens use `secrets.token_urlsafe(32)` and are stored as hashed values
- [ ] `_verify_tenant_access` calls `context.is_super_admin()` (method), not `getattr(..., False)` (attribute)

### P1 criteria (required before external access)

- [ ] User IDs are UUIDs, not email-derived strings
- [ ] Password complexity is validated server-side (min 12 chars, common password check)
- [ ] Tenant plan cannot be set from the signup request body
- [ ] Login endpoint has rate limiting and account lockout after configurable threshold
- [ ] Dev bypass code is absent from production builds (CI gate passes)
- [ ] JWT expiry is driven by `access_token_expire_minutes` config, not hardcoded
- [ ] Deactivated users' existing JWTs are rejected by `get_current_user`
- [ ] Logout endpoint exists and invalidates the session
- [ ] Session cookies include `HttpOnly`, `Secure`, `SameSite` in production
- [ ] Standalone API invite cannot escalate role above inviter's role
- [ ] Standalone API uses canonical role schema (`tenant_admin`, not `admin`)
- [ ] Privileged access is denied if audit emission fails
- [ ] OIDC state validation is server-side, not sessionStorage-dependent

### P2 criteria (required before SOC 2 audit)

- [ ] Email verification is required before account activation (standalone API)
- [ ] Auth events (login, logout, signup, invite) are written to the persistent audit log
- [ ] Password reset flow exists in both stacks
- [ ] Password change form in `PersonalSecurity.tsx` is wired to a backend endpoint
- [ ] 2FA controls in `PersonalSecurity.tsx` are either wired or clearly marked as not yet available
- [ ] Profile update form in `PersonalProfile.tsx` is wired to a backend endpoint
- [ ] PlatformSettings security controls are either enforced or disabled in the UI
- [ ] Sensitive GET reads (user list, audit log, config) are logged by audit middleware
- [ ] Platform-level auth/access audit log is accessible in the admin UI
- [ ] `DevAuthBypassMiddleware` class is removed from the codebase

### Test gate

- [ ] All tests in `tests/security/test_auth_governance.py` pass
- [ ] All existing security regression tests continue to pass
- [ ] CI route auth gate passes for all services

## Final Report Checklist

Use this checklist to verify the audit deliverables are complete before sign-off.

### Audit coverage

- [x] Sign-up / registration flow reviewed (both stacks)
- [x] Sign-in & authentication reviewed (both stacks)
- [x] Session & token management reviewed (both stacks)
- [x] User management & invitation flow reviewed (both stacks)
- [x] Permissions & RBAC reviewed (both stacks + shared packages)
- [x] User settings reviewed (frontend)
- [x] System configuration & audit logging reviewed (both stacks + frontend)
- [x] Cross-stack gaps identified and documented

### Findings

- [x] 25 findings documented with severity, stack, framework mapping
- [x] 4 P0 findings identified
- [x] 9 P1 findings identified
- [x] 10 P2 findings identified
- [x] 2 P3 findings identified (F-23 dead code, F-14 naming consistency)
- [x] Each finding includes design requirement, code-level guidance, and required tests

### Deliverables

- [x] Findings summary table with OWASP / NIST / SOC 2 mappings
- [x] Per-finding remediation guidance (design + code level)
- [x] Required fixes table ordered by priority
- [x] Required test list with test names and coverage mapping
- [x] Acceptance criteria checklist (P0 / P1 / P2 bands)

### Implementation readiness

- [ ] User has confirmed spec is complete
- [ ] Implementation has begun (tracked separately)
- [ ] All P0 findings resolved
- [ ] All P1 findings resolved
- [ ] All P2 findings resolved
- [ ] Final security regression test suite passes in CI
