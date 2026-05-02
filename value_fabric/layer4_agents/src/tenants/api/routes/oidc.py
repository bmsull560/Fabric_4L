"""OIDC SSO routes for tenant authentication with PKCE support (P0-10).

GET /auth/oidc/{tenant_slug}/login   — initiate OIDC flow with PKCE
GET /auth/oidc/callback              — handle IdP callback with PKCE verification
GET /auth/oidc/{tenant_slug}/metadata — return non-sensitive IdP config
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from shared.audit import AuditAction, AuditOutcome, emit_audit_event
from shared.identity.jwt import encode_jwt
from shared.identity.oidc_config import OIDCProviderConfig
from shared.identity.permissions import Role
from shared.models.typed_dict import TypedDictModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.identity.oidc import OIDCClient, map_role_from_claims

# SECURITY: OIDC login/callback endpoints are pre-authentication flows.
# The user does not yet have a JWT, so get_db (no tenant context) is
# intentional here. Authentication is via OIDC provider + PKCE.
from ....database import get_db_from_context
from ....api.security.csrf import CSRF_COOKIE_NAME, SESSION_COOKIE_NAME, issue_csrf_token
from ....tenants.models.tenant import Tenant
from ....tenants.models.user import User


class oidc_loginResult(TypedDictModel):
    authorization_url: Any
    state: Any

class oidc_callbackResult(TypedDictModel):
    access_token: Any
    email: Any
    expires_in: int
    role: Any
    token_type: str
    user_id: Any

class oidc_metadataResult(TypedDictModel):
    auto_provision_users: Any
    claim_mapping_keys: list[Any]
    default_role: Any
    enabled: Any
    issuer_url: Any
    provider_name: Any
    scopes: Any

router = APIRouter(prefix="/auth/oidc", tags=["OIDC SSO"])

_DEFAULT_REDIRECT_URI = os.getenv(
    "OIDC_DEFAULT_REDIRECT_URI", "https://localhost:3000/auth/callback"
)


def _generate_state() -> str:
    return secrets.token_urlsafe(32)


def _generate_nonce() -> str:
    return secrets.token_urlsafe(32)


# P0-10: PKCE helper functions
def _generate_code_verifier() -> str:
    """Generate PKCE code_verifier (43-128 chars, base64url)."""
    # RFC 7636: code_verifier is 43-128 chars of [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii").rstrip("=")


def _generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code_challenge from code_verifier using S256 method."""
    # RFC 7636: code_challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


async def _get_tenant_by_slug(db: AsyncSession, slug: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    return result.scalar_one_or_none()


async def _get_user_by_email(db: AsyncSession, tenant_id: UUID, email: str) -> User | None:
    result = await db.execute(select(User).where(User.tenant_id == tenant_id, User.email == email))
    return result.scalar_one_or_none()


async def _get_client_secret(config: OIDCProviderConfig) -> str:
    """Resolve the OIDC client secret from config reference.

    Supports:
    - Vault references: "vault:secret/data/path#key"
    - Environment variable references: "ENV_VAR_NAME"
    - Direct values (fallback)

    Raises:
        ValueError: If client secret cannot be resolved
    """
    # First try client_secret_ref if provided
    if config.client_secret_ref:
        # Handle Vault references
        if config.client_secret_ref.startswith("vault:"):
            from shared.identity.vault_check import resolve_vault_secret

            secret = await resolve_vault_secret(config.client_secret_ref)
            if secret:
                return secret
            raise ValueError(f"Failed to resolve Vault secret: {config.client_secret_ref}")
        else:
            # Treat as environment variable name
            secret = os.getenv(config.client_secret_ref)
            if secret:
                return secret
            raise ValueError(f"Environment variable not set: {config.client_secret_ref}")

    # Try fallback env var pattern
    fallback_key = f"OIDC_CLIENT_SECRET_{config.provider_name.upper()}"
    secret = os.getenv(fallback_key)
    if secret:
        return secret

    # Try direct client_secret field
    if config.client_secret:
        return config.client_secret

    raise ValueError(
        f"No client secret found. Set {fallback_key} environment variable "
        f"or configure client_secret_ref in tenant settings."
    )


@router.get("/{tenant_slug}/login")
async def oidc_login(
    tenant_slug: str,
    redirect_uri: str | None = Query(None),
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, str]:
    """Initiate OIDC login for a tenant.

    Stores state/nonce in ``oidc_sessions`` and returns the IdP authorize URL.
    """
    tenant = await _get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    oidc_config = OIDCProviderConfig.from_settings(tenant.settings or {})
    if oidc_config is None or not oidc_config.enabled:
        raise HTTPException(status_code=400, detail="OIDC is not enabled for this tenant")

    oidc_client = OIDCClient()
    try:
        metadata = await oidc_client.discover(oidc_config.issuer_url)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to discover OIDC provider: {exc}"
        ) from exc

    state = _generate_state()
    nonce = _generate_nonce()
    # P0-10: Generate PKCE parameters
    code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(code_verifier)
    final_redirect = redirect_uri or _DEFAULT_REDIRECT_URI

    # Store session with PKCE code_verifier
    from sqlalchemy import text

    await db.execute(
        text(
            """
            INSERT INTO oidc_sessions (tenant_id, state, nonce, code_verifier, redirect_uri, expires_at, use_pkce)
            VALUES (:tenant_id, :state, :nonce, :code_verifier, :redirect_uri, :expires_at, :use_pkce)
            """
        ),
        {
            "tenant_id": tenant.id,
            "state": state,
            "nonce": nonce,
            "code_verifier": code_verifier,
            "redirect_uri": final_redirect,
            "expires_at": datetime.now(UTC) + timedelta(minutes=10),
            "use_pkce": True,
        },
    )

    # P0-10: Build authorize URL with PKCE code_challenge
    auth_url = oidc_client.build_authorize_url(
        metadata=metadata,
        client_id=oidc_config.client_id,
        redirect_uri=final_redirect,
        state=state,
        nonce=nonce,
        scopes=oidc_config.scopes,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )

    return oidc_loginResult.model_validate({"authorization_url": auth_url, "state": state})


@router.get("/callback")
async def oidc_callback(
    request: Request,
    response: Response,
    state: str = Query(...),
    code: str = Query(...),
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Handle OIDC callback from the identity provider.

    Validates state, exchanges code for tokens, verifies id_token,
    maps claims to VF role, auto-provisions the user if enabled,
    and returns an internal JWT access_token.
    """
    from sqlalchemy import text

    # Look up and validate session (P0-10: include code_verifier for PKCE)
    result = await db.execute(
        text(
            """
            SELECT tenant_id, nonce, code_verifier, redirect_uri, expires_at
            FROM oidc_sessions WHERE state = :state
            """
        ),
        {"state": state},
    )
    row = result.mappings().one_or_none()
    if row is None:
        emit_audit_event(
            AuditAction.OIDC_LOGIN_FAILED,
            resource_type="OIDCSession",
            outcome=AuditOutcome.FAILURE,
            details={"reason": "invalid_state"},
        )
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")

    if row["expires_at"] < datetime.now(UTC):
        await db.execute(text("DELETE FROM oidc_sessions WHERE state = :state"), {"state": state})
        emit_audit_event(
            AuditAction.OIDC_LOGIN_FAILED,
            tenant_id=row["tenant_id"],
            resource_type="OIDCSession",
            outcome=AuditOutcome.FAILURE,
            details={"reason": "expired_state"},
        )
        raise HTTPException(status_code=400, detail="OIDC session expired")

    tenant_id: UUID = row["tenant_id"]
    nonce: str = row["nonce"]
    code_verifier: str | None = row.get("code_verifier")
    redirect_uri: str = row["redirect_uri"]

    # Clean up session
    await db.execute(text("DELETE FROM oidc_sessions WHERE state = :state"), {"state": state})

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    oidc_config = OIDCProviderConfig.from_settings(tenant.settings or {})
    if oidc_config is None or not oidc_config.enabled:
        raise HTTPException(status_code=400, detail="OIDC is not enabled for this tenant")

    client_secret = await _get_client_secret(oidc_config)
    oidc_client = OIDCClient()

    try:
        metadata = await oidc_client.discover(oidc_config.issuer_url)
        # P0-10: Pass code_verifier for PKCE verification
        token_response = await oidc_client.exchange_code(
            token_endpoint=metadata["token_endpoint"],
            code=code,
            redirect_uri=redirect_uri,
            client_id=oidc_config.client_id,
            client_secret=client_secret,
            code_verifier=code_verifier,  # PKCE parameter
        )
        id_token = token_response.get("id_token")
        if not id_token:
            raise HTTPException(status_code=502, detail="No id_token in token response")

        claims = await oidc_client.verify_id_token(
            id_token=id_token,
            issuer_url=oidc_config.issuer_url,
            client_id=oidc_config.client_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        emit_audit_event(
            AuditAction.OIDC_LOGIN_FAILED,
            tenant_id=tenant_id,
            resource_type="OIDCSession",
            outcome=AuditOutcome.FAILURE,
            details={"reason": "token_exchange_failed", "error": str(exc)},
        )
        raise HTTPException(
            status_code=502, detail=f"OIDC token verification failed: {exc}"
        ) from exc

    # Validate nonce if present in token (constant-time comparison to prevent timing attacks)
    token_nonce = claims.get("nonce")
    if token_nonce:
        import hmac

        if not hmac.compare_digest(str(token_nonce), str(nonce)):
            emit_audit_event(
                AuditAction.OIDC_LOGIN_FAILED,
                tenant_id=tenant_id,
                resource_type="OIDCSession",
                outcome=AuditOutcome.FAILURE,
                details={"reason": "nonce_mismatch"},
            )
            raise HTTPException(status_code=400, detail="OIDC nonce mismatch")

    # Map claims to role
    email = claims.get("email", "")
    mapped_role = map_role_from_claims(
        claims,
        claim_mapping=oidc_config.claim_mapping,
        default_role=oidc_config.default_role,
    )

    # Ensure mapped role is valid
    try:
        role_enum = Role(mapped_role)
    except ValueError:
        role_enum = (
            Role(oidc_config.default_role)
            if oidc_config.default_role in Role._value2member_map_
            else Role.READ_ONLY
        )
        mapped_role = role_enum.value

    # Find or auto-provision user
    user = await _get_user_by_email(db, tenant_id, email)
    if user is None:
        if oidc_config.auto_provision_users:
            user = User(
                tenant_id=tenant_id,
                email=email,
                role=mapped_role,
                status="active",
                display_name=claims.get("name") or claims.get("preferred_username"),
                hashed_password=None,
            )
            db.add(user)
            await db.flush()
        else:
            emit_audit_event(
                AuditAction.OIDC_LOGIN_FAILED,
                tenant_id=tenant_id,
                resource_type="User",
                outcome=AuditOutcome.FAILURE,
                details={"reason": "user_not_found", "email": email},
            )
            raise HTTPException(
                status_code=403, detail="User not found and auto-provisioning is disabled"
            )
    else:
        # Update role if claim mapping changed (optional behaviour)
        if user.role != mapped_role:
            user.role = mapped_role
        user.last_login_at = datetime.now(UTC)


    # Issue internal JWT
    access_token = encode_jwt(
        tenant_id=tenant_id,
        user_id=str(user.id),
        roles=[user.role],
        expires_in_seconds=3600,
    )
    csrf_token = issue_csrf_token()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="strict",
        max_age=3600,
        path="/",
    )

    emit_audit_event(
        AuditAction.OIDC_LOGIN,
        tenant_id=tenant_id,
        user_id=str(user.id),
        resource_type="User",
        resource_id=str(user.id),
        outcome=AuditOutcome.SUCCESS,
        details={"provider": oidc_config.provider_name, "email": email},
    )

    return oidc_callbackResult.model_validate({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "user_id": str(user.id),
        "email": email,
        "role": user.role,
    })


@router.get("/{tenant_slug}/metadata")
async def oidc_metadata(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Return non-sensitive OIDC configuration for a tenant."""
    tenant = await _get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    oidc_config = OIDCProviderConfig.from_settings(tenant.settings or {})
    if oidc_config is None:
        raise HTTPException(status_code=400, detail="OIDC is not configured for this tenant")

    return oidc_metadataResult.model_validate({
        "provider_name": oidc_config.provider_name,
        "issuer_url": oidc_config.issuer_url,
        "scopes": oidc_config.scopes,
        "claim_mapping_keys": list(oidc_config.claim_mapping.keys()),
        "default_role": oidc_config.default_role,
        "auto_provision_users": oidc_config.auto_provision_users,
        "enabled": oidc_config.enabled,
    })

