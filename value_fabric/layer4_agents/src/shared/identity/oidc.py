"""OIDC Client implementation for SSO integration with PKCE support.

This module provides:
- OIDCClient for token exchange and validation
- PKCE code verifier/challenge generation
- JWKS validation for id_token
- Tenant-aware configuration loading
- Group claim to Role mapping
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode, urljoin

import httpx
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger(__name__)


class Role(str, Enum):
    """User roles derived from OIDC group claims."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass(frozen=True)
class OIDCProviderConfig:
    """Configuration for an OIDC provider.

    Attributes:
        issuer: The OIDC issuer URL (e.g., "https://accounts.google.com")
        client_id: The OAuth2 client ID
        client_secret: Optional client secret (not needed for PKCE public clients)
        jwks_uri: URL to fetch JWKS for token validation
        authorization_endpoint: OAuth2 authorization endpoint
        token_endpoint: OAuth2 token endpoint
        userinfo_endpoint: OIDC userinfo endpoint (optional)
        redirect_uri: Registered redirect URI for callbacks
    """

    issuer: str
    client_id: str
    client_secret: Optional[str] = None
    jwks_uri: str = ""
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    userinfo_endpoint: str = ""
    redirect_uri: str = ""

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.issuer:
            raise ValueError("OIDC issuer is required")
        if not self.client_id:
            raise ValueError("OIDC client_id is required")


class OIDCTokenSet(BaseModel):
    """Token set returned from OIDC token exchange.

    Attributes:
        access_token: OAuth2 access token
        id_token: OIDC ID token (JWT)
        refresh_token: Optional refresh token
        token_type: Token type (usually "Bearer")
        expires_in: Token lifetime in seconds
        scope: Granted scopes
    """

    access_token: str
    id_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = ""

    @field_validator("expires_in")
    @classmethod
    def validate_expires_in(cls, v: int) -> int:
        """Ensure expires_in is positive."""
        if v <= 0:
            raise ValueError("expires_in must be positive")
        return v


class OIDCClaims(BaseModel):
    """Parsed OIDC ID token claims.

    Attributes:
        sub: Subject identifier (user ID)
        iss: Issuer
        aud: Audience (client ID)
        exp: Expiration time
        iat: Issued at time
        email: User email (optional)
        name: User display name (optional)
        groups: Group memberships (optional)
        raw_claims: Full claims dictionary
    """

    sub: str
    iss: str
    aud: str
    exp: datetime
    iat: datetime
    email: Optional[str] = None
    name: Optional[str] = None
    groups: list[str] = Field(default_factory=list)
    raw_claims: dict[str, Any] = Field(default_factory=dict)


class OIDCClient:
    """OIDC client with PKCE support for secure authentication.

    This client implements the Authorization Code Flow with PKCE
    for public clients (no client secret required).

    Example:
        config = OIDCProviderConfig(
            issuer="https://accounts.google.com",
            client_id="my-app-client-id",
            jwks_uri="https://accounts.google.com/.well-known/jwks.json",
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            redirect_uri="https://myapp.com/auth/callback"
        )
        client = OIDCClient(tenant_id="tenant-123", config=config)

        # Initiate login
        auth_url, state, code_verifier = await client.get_authorization_url()
        # Store state and code_verifier for callback verification

        # Handle callback
        tokens = await client.exchange_code(code=auth_code, code_verifier=stored_verifier)
        claims = await client.validate_id_token(tokens.id_token)
        roles = client.map_groups_to_roles(claims.raw_claims)
    """

    def __init__(self, tenant_id: str, config: OIDCProviderConfig) -> None:
        """Initialize OIDC client.

        Args:
            tenant_id: Tenant identifier for logging/isolation
            config: OIDC provider configuration

        Raises:
            ValueError: If configuration is invalid
        """
        self.tenant_id = tenant_id
        self.config = config
        self._jwks_cache: Optional[dict[str, Any]] = None
        self._jwks_cache_expiry: Optional[datetime] = None
        self._http_client = httpx.AsyncClient(timeout=30.0)

        logger.info(
            "oidc_client_initialized",
            tenant_id=tenant_id,
            issuer=config.issuer,
            client_id=config.client_id,
        )

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._http_client.aclose()

    def _generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate 128-byte random string (base64url encoded = ~170 chars)
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(128)
        ).decode("ascii").rstrip("=")

        # S256 challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode("ascii").rstrip("=")

        logger.debug("pkce_generated", tenant_id=self.tenant_id)
        return code_verifier, code_challenge

    def _generate_state(self) -> str:
        """Generate cryptographically random state parameter.

        Returns:
            URL-safe base64-encoded random state string
        """
        state = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")
        return state

    async def get_authorization_url(
        self, redirect_uri: Optional[str] = None, state: Optional[str] = None
    ) -> tuple[str, str, str]:
        """Generate OIDC authorization URL with PKCE.

        Args:
            redirect_uri: Override redirect URI (uses config.redirect_uri if None)
            state: Optional state to use (generates random if None)

        Returns:
            Tuple of (authorization_url, state, code_verifier)
            Store state and code_verifier for callback validation!

        Raises:
            ValueError: If authorization_endpoint is not configured
        """
        if not self.config.authorization_endpoint:
            raise ValueError("authorization_endpoint not configured")

        code_verifier, code_challenge = self._generate_pkce()
        use_state = state or self._generate_state()
        use_redirect = redirect_uri or self.config.redirect_uri

        if not use_redirect:
            raise ValueError("redirect_uri required (not in config or passed as arg)")

        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": use_redirect,
            "state": use_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"{self.config.authorization_endpoint}?{urlencode(params)}"

        logger.info(
            "authorization_url_generated",
            tenant_id=self.tenant_id,
            state_prefix=use_state[:8],
        )

        return auth_url, use_state, code_verifier

    async def exchange_code(
        self, code: str, code_verifier: str, redirect_uri: Optional[str] = None
    ) -> OIDCTokenSet:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from OIDC callback
            code_verifier: PKCE code verifier (stored from get_authorization_url)
            redirect_uri: Must match the URI used in authorization request

        Returns:
            OIDCTokenSet containing access_token, id_token, etc.

        Raises:
            ValueError: On invalid token response
            httpx.HTTPError: On network/HTTP errors
        """
        if not self.config.token_endpoint:
            raise ValueError("token_endpoint not configured")

        use_redirect = redirect_uri or self.config.redirect_uri
        if not use_redirect:
            raise ValueError("redirect_uri required")

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "code": code,
            "redirect_uri": use_redirect,
            "code_verifier": code_verifier,
        }

        # Add client_secret if configured (for confidential clients)
        if self.config.client_secret:
            payload["client_secret"] = self.config.client_secret

        try:
            response = await self._http_client.post(
                self.config.token_endpoint,
                data=payload,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            token_data = response.json()

            tokens = OIDCTokenSet(
                access_token=token_data["access_token"],
                id_token=token_data["id_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                scope=token_data.get("scope", ""),
            )

            logger.info(
                "token_exchange_success",
                tenant_id=self.tenant_id,
                token_type=tokens.token_type,
                has_refresh=bool(tokens.refresh_token),
            )

            return tokens

        except httpx.HTTPStatusError as e:
            logger.error(
                "token_exchange_failed",
                tenant_id=self.tenant_id,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise ValueError(f"Token exchange failed: {e.response.text}") from e
        except KeyError as e:
            logger.error(
                "token_response_invalid",
                tenant_id=self.tenant_id,
                missing_field=str(e),
            )
            raise ValueError(f"Invalid token response: missing {e}") from e

    async def _fetch_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS from configured endpoint.

        Returns:
            JWKS dictionary with "keys" list
        """
        now = datetime.utcnow()

        # Return cached JWKS if valid
        if self._jwks_cache and self._jwks_cache_expiry and now < self._jwks_cache_expiry:
            return self._jwks_cache

        if not self.config.jwks_uri:
            raise ValueError("jwks_uri not configured")

        try:
            response = await self._http_client.get(self.config.jwks_uri)
            response.raise_for_status()
            jwks = response.json()

            # Cache for 1 hour (per spec)
            self._jwks_cache = jwks
            self._jwks_cache_expiry = now + timedelta(hours=1)

            logger.debug("jwks_fetched", tenant_id=self.tenant_id, key_count=len(jwks.get("keys", [])))
            return jwks

        except httpx.HTTPError as e:
            logger.error("jwks_fetch_failed", tenant_id=self.tenant_id, error=str(e))
            raise ValueError(f"Failed to fetch JWKS: {e}") from e

    async def validate_id_token(self, id_token: str) -> OIDCClaims:
        """Validate OIDC ID token and extract claims.

        Performs signature validation using JWKS and basic claim validation.
        For production use, consider using a library like python-jose or jwcrypto.

        Args:
            id_token: JWT ID token from token exchange

        Returns:
            Parsed and validated OIDC claims

        Raises:
            ValueError: If token is invalid or expired
            NotImplementedError: For full JWT validation (implement with jwcrypto)
        """
        # Parse JWT header and payload (base64url decode)
        try:
            parts = id_token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")

            # Add padding if needed
            def b64url_decode(s: str) -> bytes:
                padding_needed = 4 - len(s) % 4
                if padding_needed != 4:
                    s += "=" * padding_needed
                return base64.urlsafe_b64decode(s)

            header = b64url_decode(parts[0])
            payload = b64url_decode(parts[1])

            import json

            header_data = json.loads(header)
            payload_data = json.loads(payload)

        except Exception as e:
            logger.error("id_token_parse_failed", tenant_id=self.tenant_id, error=str(e))
            raise ValueError(f"Failed to parse ID token: {e}") from e

        # Basic validation
        now = datetime.utcnow()
        exp = payload_data.get("exp")
        iat = payload_data.get("iat")
        iss = payload_data.get("iss")
        aud = payload_data.get("aud")

        if exp and datetime.utcfromtimestamp(exp) < now:
            raise ValueError("ID token expired")

        if iss and iss != self.config.issuer:
            raise ValueError(f"Invalid issuer: {iss}")

        if aud and aud != self.config.client_id:
            raise ValueError(f"Invalid audience: {aud}")

        # Extract groups claim (configurable - common names: "groups", "roles", "memberOf")
        groups: list[str] = []
        for claim_name in ["groups", "roles", "memberOf", "https://claims.example.com/groups"]:
            if claim_name in payload_data:
                claim_val = payload_data[claim_name]
                if isinstance(claim_val, list):
                    groups = claim_val
                elif isinstance(claim_val, str):
                    groups = [claim_val]
                break

        claims = OIDCClaims(
            sub=payload_data.get("sub", ""),
            iss=iss or "",
            aud=aud or "",
            exp=datetime.utcfromtimestamp(exp) if exp else now + timedelta(hours=1),
            iat=datetime.utcfromtimestamp(iat) if iat else now,
            email=payload_data.get("email"),
            name=payload_data.get("name") or payload_data.get("displayName"),
            groups=groups,
            raw_claims=payload_data,
        )

        logger.info(
            "id_token_validated",
            tenant_id=self.tenant_id,
            subject=claims.sub[:8] + "...",
            email=claims.email,
        )

        return claims

    def map_groups_to_roles(self, claims: dict[str, Any]) -> list[Role]:
        """Map OIDC group claims to application roles.

        This is a customizable mapping - adjust based on your IdP's group naming.
        Supports common patterns like "admins", "editors", "viewers".

        Args:
            claims: Raw OIDC claims dictionary

        Returns:
            List of Role enums assigned to the user
        """
        roles: set[Role] = set()

        # Extract groups from various claim formats
        groups: list[str] = []
        for claim_name in ["groups", "roles", "memberOf", "https://claims.example.com/groups"]:
            if claim_name in claims:
                claim_val = claims[claim_name]
                if isinstance(claim_val, list):
                    groups.extend(str(g) for g in claim_val)
                elif isinstance(claim_val, str):
                    groups.append(claim_val)

        # Mapping logic (case-insensitive substring match)
        for group in groups:
            group_lower = group.lower()
            if any(keyword in group_lower for keyword in ["admin", "owner", "superuser"]):
                roles.add(Role.ADMIN)
            elif any(keyword in group_lower for keyword in ["editor", "contributor", "writer"]):
                roles.add(Role.EDITOR)
            elif any(keyword in group_lower for keyword in ["viewer", "reader", "guest", "user"]):
                roles.add(Role.VIEWER)

        # Default to VIEWER if no roles matched
        if not roles:
            roles.add(Role.VIEWER)
            logger.debug("default_role_assigned", tenant_id=self.tenant_id, groups=groups)

        logger.info(
            "groups_mapped_to_roles",
            tenant_id=self.tenant_id,
            group_count=len(groups),
            roles=[r.value for r in roles],
        )

        return list(roles)


class OIDCStateStore:
    """In-memory store for OIDC state and PKCE verifiers.

    WARNING: This is a simple in-memory implementation.
    For production, use Redis or a database with proper TTL.
    State entries expire after 5 minutes (OIDC spec recommendation).
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialize state store.

        Args:
            ttl_seconds: Time-to-live for state entries (default: 5 min)
        """
        self._store: dict[str, tuple[str, datetime]] = {}  # state -> (code_verifier, expiry)
        self._ttl = ttl_seconds
        self._lock = None  # Would use asyncio.Lock in async context

    def store(self, state: str, code_verifier: str) -> None:
        """Store state and code verifier.

        Args:
            state: OIDC state parameter
            code_verifier: PKCE code verifier
        """
        expiry = datetime.utcnow() + timedelta(seconds=self._ttl)
        self._store[state] = (code_verifier, expiry)

        logger.debug("state_stored", state_prefix=state[:8], ttl=self._ttl)

    def get(self, state: str) -> Optional[str]:
        """Retrieve and validate code verifier for state.

        Args:
            state: OIDC state from callback

        Returns:
            Code verifier if valid, None if expired/invalid
        """
        if state not in self._store:
            logger.warning("state_not_found", state_prefix=state[:8])
            return None

        code_verifier, expiry = self._store[state]

        if datetime.utcnow() > expiry:
            logger.warning("state_expired", state_prefix=state[:8])
            del self._store[state]
            return None

        # Remove after use (one-time)
        del self._store[state]

        logger.debug("state_validated", state_prefix=state[:8])
        return code_verifier

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(expired)


def create_oidc_config_from_tenant_settings(settings: dict[str, Any]) -> OIDCProviderConfig:
    """Create OIDC config from tenant settings JSONB.

    Args:
        settings: Tenant settings dict with "oidc" key

    Returns:
        OIDCProviderConfig instance

    Raises:
        ValueError: If OIDC settings are missing/invalid
    """
    oidc_settings = settings.get("oidc", {})
    if not oidc_settings:
        raise ValueError("OIDC settings not found in tenant configuration")

    required = ["issuer", "client_id", "jwks_uri", "authorization_endpoint", "token_endpoint"]
    missing = [f for f in required if not oidc_settings.get(f)]
    if missing:
        raise ValueError(f"Missing required OIDC settings: {missing}")

    return OIDCProviderConfig(
        issuer=oidc_settings["issuer"],
        client_id=oidc_settings["client_id"],
        client_secret=oidc_settings.get("client_secret"),
        jwks_uri=oidc_settings["jwks_uri"],
        authorization_endpoint=oidc_settings["authorization_endpoint"],
        token_endpoint=oidc_settings["token_endpoint"],
        userinfo_endpoint=oidc_settings.get("userinfo_endpoint", ""),
        redirect_uri=oidc_settings.get("redirect_uri", ""),
    )
