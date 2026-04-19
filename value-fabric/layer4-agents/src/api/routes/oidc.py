"""OIDC authentication routes for FastAPI.

Provides endpoints for initiating OIDC login and handling callbacks.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from shared.identity.oidc import (
    OIDCClient,
    OIDCProviderConfig,
    OIDCStateStore,
    Role,
    create_oidc_config_from_tenant_settings,
)

logger = structlog.get_logger(__name__)

# In-memory state store - use Redis in production
_state_store = OIDCStateStore(ttl_seconds=300)

router = APIRouter(prefix="/auth/oidc", tags=["Authentication"])


class LoginInitResponse(BaseModel):
    """Response for login initiation endpoint."""

    authorization_url: str = Field(..., description="URL to redirect user for authentication")
    state: str = Field(..., description="State parameter - store for callback validation")
    message: str = Field(default="Redirect user to authorization_url")


class CallbackResponse(BaseModel):
    """Response for successful OIDC callback."""

    access_token: str = Field(..., description="Access token for API calls")
    id_token: str = Field(..., description="OIDC ID token (JWT)")
    refresh_token: str | None = Field(None, description="Refresh token (if issued)")
    token_type: str = Field(default="Bearer")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    roles: list[str] = Field(..., description="User roles from group claims")
    user_id: str = Field(..., description="User subject identifier")
    email: str | None = Field(None, description="User email")


class ErrorResponse(BaseModel):
    """Error response for OIDC failures."""

    error: str = Field(..., description="Error code")
    error_description: str = Field(..., description="Human-readable error description")


async def get_tenant_from_path(tenant: str) -> str:
    """Extract and validate tenant ID from path parameter.

    Args:
        tenant: Tenant identifier from URL path

    Returns:
        Validated tenant ID

    Raises:
        HTTPException: If tenant ID is invalid
    """
    if not tenant or not tenant.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant identifier",
        )
    return tenant


def get_oidc_config_for_tenant(tenant_id: str) -> OIDCProviderConfig:
    """Fetch OIDC configuration for tenant from database.

    Args:
        tenant_id: Tenant identifier

    Returns:
        OIDC provider configuration

    Raises:
        HTTPException: If OIDC not configured for tenant
    """
    # TODO: Fetch from database - tenants.settings JSONB column
    # For now, check environment variable for development
    import os

    tenant_settings_env = os.getenv(f"TENANT_{tenant_id.upper().replace('-', '_')}_OIDC")
    if tenant_settings_env:
        import json

        settings = {"oidc": json.loads(tenant_settings_env)}
        return create_oidc_config_from_tenant_settings(settings)

    # Fallback: try to load from tenant record in DB (not implemented here)
    # from database import get_tenant_settings
    # settings = get_tenant_settings(tenant_id)
    # return create_oidc_config_from_tenant_settings(settings)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"OIDC not configured for tenant: {tenant_id}",
    )


@router.get(
    "/{tenant}/login",
    response_model=LoginInitResponse,
    responses={
        404: {"model": ErrorResponse, "description": "OIDC not configured for tenant"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def oidc_login(
    request: Request,
    tenant: str,
    redirect_uri: str | None = None,
) -> LoginInitResponse:
    """Initiate OIDC login flow.

    Generates authorization URL with PKCE. Store the returned state
    and use the code_verifier when handling the callback.

    Args:
        request: FastAPI request object
        tenant: Tenant identifier
        redirect_uri: Optional override for redirect URI

    Returns:
        LoginInitResponse with authorization_url and state
    """
    tenant_id = await get_tenant_from_path(tenant)

    try:
        config = get_oidc_config_for_tenant(tenant_id)
        client = OIDCClient(tenant_id=tenant_id, config=config)

        # Use redirect_uri from query param or config
        use_redirect = redirect_uri or config.redirect_uri
        if not use_redirect:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="redirect_uri required (not configured for tenant)",
            )

        auth_url, state, code_verifier = await client.get_authorization_url(
            redirect_uri=use_redirect
        )

        # Store state -> code_verifier mapping
        _state_store.store(state, code_verifier)

        # Log with context for audit
        logger.info(
            "oidc_login_initiated",
            tenant_id=tenant_id,
            state_prefix=state[:8],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return LoginInitResponse(
            authorization_url=auth_url,
            state=state,
            message="Redirect user to authorization_url within 5 minutes",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("oidc_login_failed", tenant_id=tenant_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OIDC login",
        ) from e


@router.post(
    "/callback",
    response_model=CallbackResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid callback parameters"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def oidc_callback(
    request: Request,
    code: str,
    state: str,
    tenant: str,
    redirect_uri: str | None = None,
) -> CallbackResponse:
    """Handle OIDC callback after user authentication.

    Exchanges authorization code for tokens and validates user identity.

    Args:
        request: FastAPI request object
        code: Authorization code from OIDC provider
        state: State parameter (must match login initiation)
        tenant: Tenant identifier
        redirect_uri: Must match the URI used in login request

    Returns:
        CallbackResponse with tokens and user info
    """
    tenant_id = await get_tenant_from_path(tenant)

    # Retrieve code_verifier from state store
    code_verifier = _state_store.get(state)
    if not code_verifier:
        logger.warning(
            "oidc_callback_invalid_state",
            tenant_id=tenant_id,
            state_prefix=state[:8],
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )

    try:
        config = get_oidc_config_for_tenant(tenant_id)
        client = OIDCClient(tenant_id=tenant_id, config=config)

        # Exchange code for tokens
        tokens = await client.exchange_code(
            code=code, code_verifier=code_verifier, redirect_uri=redirect_uri
        )

        # Validate ID token and extract claims
        claims = await client.validate_id_token(tokens.id_token)

        # Map groups to roles
        roles = client.map_groups_to_roles(claims.raw_claims)

        # Log successful authentication for audit
        logger.info(
            "oidc_login_success",
            tenant_id=tenant_id,
            user_id=claims.sub,
            email=claims.email,
            roles=[r.value for r in roles],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return CallbackResponse(
            access_token=tokens.access_token,
            id_token=tokens.id_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
            roles=[r.value for r in roles],
            user_id=claims.sub,
            email=claims.email,
        )

    except ValueError as e:
        logger.error(
            "oidc_callback_validation_failed",
            tenant_id=tenant_id,
            error=str(e),
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {e}",
        ) from e
    except Exception as e:
        logger.error("oidc_callback_failed", tenant_id=tenant_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication callback failed",
        ) from e


@router.get("/callback")
async def oidc_callback_get(
    request: Request,
    code: str,
    state: str,
    tenant: str,
    redirect_uri: str | None = None,
) -> CallbackResponse:
    """GET handler for OIDC callback (some IdPs use GET).

    Delegates to POST handler for processing.
    """
    return await oidc_callback(request, code, state, tenant, redirect_uri)


@router.post("/logout")
async def oidc_logout(request: Request) -> JSONResponse:
    """Handle user logout (client-side token discard).

    Note: Full OIDC RP-Initiated Logout would redirect to IdP logout endpoint.
    For now, we just acknowledge the logout for audit logging.
    """
    # TODO: Add token to revocation list if implementing server-side logout

    logger.info(
        "oidc_logout",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return JSONResponse(
        content={"message": "Logout successful - discard tokens client-side"},
        status_code=200,
    )
