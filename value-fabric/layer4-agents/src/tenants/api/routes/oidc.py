"""OIDC SSO routes for tenant authentication.

GET /auth/oidc/{tenant_slug}/login   — initiate OIDC flow
GET /auth/oidc/callback              — handle IdP callback
GET /auth/oidc/{tenant_slug}/metadata — return non-sensitive IdP config
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit import emit_audit_event, AuditAction, AuditOutcome
from shared.identity.jwt import encode_jwt
from shared.identity.oidc import OIDCClient, map_role_from_claims
from shared.identity.oidc_config import OIDCProviderConfig
from shared.identity.permissions import Role

from ....database import get_db
from ....tenants.models.tenant import Tenant
from ....tenants.models.user import User

router = APIRouter(prefix="/auth/oidc", tags=["OIDC SSO"])

_DEFAULT_REDIRECT_URI = os.getenv(
    "OIDC_DEFAULT_REDIRECT_URI", "https://localhost:3000/auth/callback"
)


def _generate_state() -> str:
    return secrets.token_urlsafe(32)


def _generate_nonce() -> str:
    return secrets.token_urlsafe(32)


async def _get_tenant_by_slug(db: AsyncSession, slug: str) -> Optional[Tenant]:
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    return result.scalar_one_or_none()


async def _get_user_by_email(
    db: AsyncSession, tenant_id: UUID, email: str
) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == email)
    )
    return result.scalar_one_or_none()


def _get_client_secret(config: OIDCProviderConfig) -> str:
    """Resolve the OIDC client secret from config reference."""
    if config.client_secret_ref:
        secret = os.getenv(config.client_secret_ref)
        if secret:
            return secret
    # Fallback env var pattern
    return os.getenv(f"OIDC_CLIENT_SECRET_{config.provider_name.upper()}", "")


@router.get("/{tenant_slug}/login")
async def oidc_login(
    tenant_slug: str,
    redirect_uri: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
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
    final_redirect = redirect_uri or _DEFAULT_REDIRECT_URI

    # Store session
    from sqlalchemy import text

    await db.execute(
        text(
            """
            INSERT INTO oidc_sessions (tenant_id, state, nonce, redirect_uri, expires_at)
            VALUES (:tenant_id, :state, :nonce, :redirect_uri, :expires_at)
            """
        ),
        {
            "tenant_id": tenant.id,
            "state": state,
            "nonce": nonce,
            "redirect_uri": final_redirect,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        },
    )
    await db.commit()

    auth_url = oidc_client.build_authorize_url(
        metadata=metadata,
        client_id=oidc_config.client_id,
        redirect_uri=final_redirect,
        state=state,
        nonce=nonce,
        scopes=oidc_config.scopes,
    )

    return {"authorization_url": auth_url, "state": state}


@router.get("/callback")
async def oidc_callback(
    request: Request,
    state: str = Query(...),
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle OIDC callback from the identity provider.

    Validates state, exchanges code for tokens, verifies id_token,
    maps claims to VF role, auto-provisions the user if enabled,
    and returns an internal JWT access_token.
    """
    from sqlalchemy import text

    # Look up and validate session
    result = await db.execute(
        text(
            """
            SELECT tenant_id, nonce, redirect_uri, expires_at
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

    if row["expires_at"] < datetime.now(timezone.utc):
        await db.execute(
            text("DELETE FROM oidc_sessions WHERE state = :state"), {"state": state}
        )
        await db.commit()
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
    redirect_uri: str = row["redirect_uri"]

    # Clean up session
    await db.execute(
        text("DELETE FROM oidc_sessions WHERE state = :state"), {"state": state}
    )

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    oidc_config = OIDCProviderConfig.from_settings(tenant.settings or {})
    if oidc_config is None or not oidc_config.enabled:
        raise HTTPException(status_code=400, detail="OIDC is not enabled for this tenant")

    client_secret = _get_client_secret(oidc_config)
    oidc_client = OIDCClient()

    try:
        metadata = await oidc_client.discover(oidc_config.issuer_url)
        token_response = await oidc_client.exchange_code(
            token_endpoint=metadata["token_endpoint"],
            code=code,
            redirect_uri=redirect_uri,
            client_id=oidc_config.client_id,
            client_secret=client_secret,
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

    # Validate nonce if present in token
    token_nonce = claims.get("nonce")
    if token_nonce and token_nonce != nonce:
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
        role_enum = Role(oidc_config.default_role) if oidc_config.default_role in Role._value2member_map_ else Role.READ_ONLY
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
            raise HTTPException(status_code=403, detail="User not found and auto-provisioning is disabled")
    else:
        # Update role if claim mapping changed (optional behaviour)
        if user.role != mapped_role:
            user.role = mapped_role
        user.last_login_at = datetime.now(timezone.utc)

    await db.commit()

    # Issue internal JWT
    access_token = encode_jwt(
        tenant_id=tenant_id,
        user_id=str(user.id),
        roles=[user.role],
        expires_in_seconds=3600,
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

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "user_id": str(user.id),
        "email": email,
        "role": user.role,
    }


@router.get("/{tenant_slug}/metadata")
async def oidc_metadata(
    tenant_slug: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return non-sensitive OIDC configuration for a tenant."""
    tenant = await _get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    oidc_config = OIDCProviderConfig.from_settings(tenant.settings or {})
    if oidc_config is None:
        raise HTTPException(status_code=400, detail="OIDC is not configured for this tenant")

    return {
        "provider_name": oidc_config.provider_name,
        "issuer_url": oidc_config.issuer_url,
        "scopes": oidc_config.scopes,
        "claim_mapping_keys": list(oidc_config.claim_mapping.keys()),
        "default_role": oidc_config.default_role,
        "auto_provision_users": oidc_config.auto_provision_users,
        "enabled": oidc_config.enabled,
    }
