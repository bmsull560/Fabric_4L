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
import inspect
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx
import jwt
import structlog
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
    client_secret: str | None = None
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
    refresh_token: str | None = None
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
    email: str | None = None
    name: str | None = None
    groups: list[str] = Field(default_factory=list)
    raw_claims: dict[str, Any] = Field(default_factory=dict)


class OIDCValidationError(ValueError):
    """Structured OIDC token validation error with stable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


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
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cache_expiry: datetime | None = None
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._allowed_algorithms = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}

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
        self, redirect_uri: str | None = None, state: str | None = None
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
        self, code: str, code_verifier: str, redirect_uri: str | None = None
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

    async def _fetch_jwks(self, *, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch and cache JWKS from configured endpoint.

        Returns:
            JWKS dictionary with "keys" list
        """
        now = datetime.now(UTC)

        # Return cached JWKS if valid
        if (
            not force_refresh
            and self._jwks_cache
            and self._jwks_cache_expiry
            and now < self._jwks_cache_expiry
        ):
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

    async def _load_jwks_for_validation(self, *, force_refresh: bool = False) -> dict[str, Any]:
        """Load JWKS while tolerating test doubles that omit force_refresh."""
        try:
            result = self._fetch_jwks(force_refresh=force_refresh)
        except TypeError:
            result = self._fetch_jwks()
        if inspect.isawaitable(result):
            return await result
        return result

    def _public_key_from_jwk(self, alg: str, jwk_data: dict[str, Any]) -> Any:
        if alg.startswith("RS"):
            return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_data)
        if alg.startswith("ES"):
            return jwt.algorithms.ECAlgorithm.from_jwk(jwk_data)
        raise OIDCValidationError("oidc.id_token.invalid_alg", f"invalid_id_token: algorithm '{alg}' is not allowed")

    async def validate_id_token(
        self,
        id_token: str,
        *,
        expected_nonce: str | None = None,
        callback_state: str | None = None,
        stored_state: str | None = None,
        max_iat_age_seconds: int = 600,
    ) -> OIDCClaims:
        """Validate OIDC ID token and extract claims with strict contract checks."""
        try:
            header = jwt.get_unverified_header(id_token)
        except jwt.PyJWTError as exc:
            raise OIDCValidationError("oidc.id_token.invalid_format", "invalid_id_token: malformed_token") from exc

        alg = header.get("alg")
        if alg not in self._allowed_algorithms:
            raise OIDCValidationError(
                "oidc.id_token.invalid_alg",
                f"invalid_id_token: algorithm '{alg}' is not allowed",
            )

        kid = header.get("kid")
        if not kid:
            raise OIDCValidationError("oidc.id_token.missing_kid", "invalid_id_token: missing kid")

        jwks = await self._load_jwks_for_validation()
        keys = {key.get("kid"): key for key in jwks.get("keys", []) if key.get("kid")}
        if kid not in keys:
            self._jwks_cache = None
            self._jwks_cache_expiry = None
            jwks = await self._load_jwks_for_validation(force_refresh=True)
            keys = {key.get("kid"): key for key in jwks.get("keys", []) if key.get("kid")}
            if kid not in keys:
                raise OIDCValidationError(
                    "oidc.id_token.stale_jwks",
                    "invalid_id_token: stale JWKS or unknown key id",
                )

        try:
            public_key = self._public_key_from_jwk(alg, keys[kid])
        except Exception as exc:
            raise OIDCValidationError("oidc.id_token.invalid_jwk", "invalid_id_token: invalid JWK") from exc

        try:
            payload_data = jwt.decode(
                id_token,
                key=public_key,
                algorithms=[alg],
                audience=self.config.client_id,
                issuer=self.config.issuer,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise OIDCValidationError("oidc.id_token.expired", "invalid_id_token: expired_token") from exc
        except jwt.InvalidAudienceError as exc:
            raise OIDCValidationError("oidc.id_token.invalid_aud", "invalid_id_token: audience mismatch") from exc
        except jwt.InvalidIssuerError as exc:
            raise OIDCValidationError("oidc.id_token.invalid_iss", "invalid_id_token: issuer mismatch") from exc
        except jwt.PyJWTError as exc:
            raise OIDCValidationError(
                "oidc.id_token.invalid_signature",
                "invalid_id_token: signature validation failed",
            ) from exc

        now = datetime.now(UTC)
        iat_dt = datetime.fromtimestamp(payload_data["iat"], tz=UTC)
        if iat_dt > now + timedelta(seconds=30):
            raise OIDCValidationError("oidc.id_token.invalid_iat", "invalid_id_token: iat is in the future")
        if iat_dt < now - timedelta(seconds=max_iat_age_seconds):
            raise OIDCValidationError("oidc.id_token.stale_iat", "invalid_id_token: iat is too old")

        if expected_nonce is not None and payload_data.get("nonce") != expected_nonce:
            raise OIDCValidationError("oidc.id_token.invalid_nonce", "invalid_id_token: nonce mismatch")

        if callback_state is not None and stored_state is not None and callback_state != stored_state:
            raise OIDCValidationError("oidc.state.replay_or_mismatch", "OIDC callback state mismatch or replay detected")

        groups: list[str] = []
        for claim_name in ["groups", "roles", "memberOf", "https://claims.example.com/groups"]:
            if claim_name in payload_data:
                claim_val = payload_data[claim_name]
                groups = claim_val if isinstance(claim_val, list) else [claim_val]
                break

        claims = OIDCClaims(
            sub=payload_data["sub"],
            iss=payload_data["iss"],
            aud=payload_data["aud"] if isinstance(payload_data["aud"], str) else payload_data["aud"][0],
            exp=datetime.fromtimestamp(payload_data["exp"], tz=UTC),
            iat=iat_dt,
            email=payload_data.get("email"),
            name=payload_data.get("name") or payload_data.get("displayName"),
            groups=[str(g) for g in groups],
            raw_claims=payload_data,
        )
        return claims

    async def verify_id_token(self, id_token: str) -> dict[str, Any]:
        """Compatibility wrapper that enforces the shared validation path."""
        claims = await self.validate_id_token(id_token)
        return claims.raw_claims

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


class OIDCStateStoreProtocol(Protocol):
    """Protocol for storing and consuming OIDC state and PKCE verifiers."""

    def store(self, state: str, code_verifier: str) -> None:
        """Store the verifier with strict TTL semantics."""

    def validate_and_consume(self, state: str) -> str | None:
        """Atomically validate and consume state for single-use semantics."""


class InMemoryOIDCStateStore(OIDCStateStoreProtocol):
    """In-memory store for tests/development only.

    This store is explicitly non-production and guarded by ``allow_non_production``.
    """

    def __init__(self, ttl_seconds: int = 300, *, allow_non_production: bool = False) -> None:
        if not allow_non_production:
            raise RuntimeError(
                "InMemoryOIDCStateStore is for tests/development only. "
                "Use RedisOIDCStateStore in production."
            )
        self._store: dict[str, tuple[str, datetime]] = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def store(self, state: str, code_verifier: str) -> None:
        expiry = datetime.now(UTC) + timedelta(seconds=self._ttl)
        with self._lock:
            self._store[state] = (code_verifier, expiry)
        logger.debug("oidc_state_stored_memory", state_prefix=state[:8], ttl=self._ttl)

    def validate_and_consume(self, state: str) -> str | None:
        now = datetime.now(UTC)
        with self._lock:
            record = self._store.get(state)
            if record is None:
                logger.warning("oidc_state_not_found_memory", state_prefix=state[:8])
                return None
            code_verifier, expiry = record
            if now > expiry:
                del self._store[state]
                logger.warning("oidc_state_expired_memory", state_prefix=state[:8])
                return None
            del self._store[state]
        logger.debug("oidc_state_consumed_memory", state_prefix=state[:8])
        return code_verifier


class RedisOIDCStateStore(OIDCStateStoreProtocol):
    """Redis-backed OIDC state store with atomic consume semantics."""

    def __init__(self, redis_client: Any, ttl_seconds: int = 300, *, key_prefix: str = "oidc:state") -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds
        self._key_prefix = key_prefix

    def _key(self, state: str) -> str:
        return f"{self._key_prefix}:{state}"

    def store(self, state: str, code_verifier: str) -> None:
        self._redis.set(self._key(state), code_verifier, ex=self._ttl)
        logger.debug("oidc_state_stored_redis", state_prefix=state[:8], ttl=self._ttl)

    def validate_and_consume(self, state: str) -> str | None:
        key = self._key(state)
        try:
            verifier = self._redis.getdel(key)
        except AttributeError:
            verifier = self._redis.eval(
                "local v = redis.call('GET', KEYS[1]); if v then redis.call('DEL', KEYS[1]); end; return v",
                1,
                key,
            )

        if verifier is None:
            logger.warning("oidc_state_not_found_or_expired_redis", state_prefix=state[:8])
            return None

        if isinstance(verifier, bytes):
            verifier = verifier.decode("utf-8")

        logger.debug("oidc_state_consumed_redis", state_prefix=state[:8])
        return str(verifier)


class OIDCStateStore(RedisOIDCStateStore):
    """Default production OIDC state store implementation (Redis-backed)."""


def create_oidc_state_store(
    *,
    redis_client: Any | None,
    ttl_seconds: int = 300,
    backend: str = "redis",
    allow_non_production_memory: bool = False,
) -> OIDCStateStoreProtocol:
    """Create OIDC state store using configured backend.

    Redis is the production default. In-memory backend requires explicit non-prod guard.
    """

    normalized = backend.strip().lower()
    if normalized == "memory":
        return InMemoryOIDCStateStore(
            ttl_seconds=ttl_seconds,
            allow_non_production=allow_non_production_memory,
        )

    if redis_client is None:
        raise RuntimeError("OIDC state store requires Redis client when backend=redis")

    return RedisOIDCStateStore(redis_client=redis_client, ttl_seconds=ttl_seconds)


def validate_tenant_oidc_provider_mapping(
    *,
    tenant_id: str,
    expected_issuer: str,
    expected_client_id: str,
    provider_config: OIDCProviderConfig,
) -> None:
    """Prevent cross-tenant OIDC provider config bleed by strict equality checks."""
    if provider_config.issuer != expected_issuer:
        raise OIDCValidationError(
            "oidc.tenant.invalid_issuer_mapping",
            f"Tenant {tenant_id} issuer mapping mismatch",
        )
    if provider_config.client_id != expected_client_id:
        raise OIDCValidationError(
            "oidc.tenant.invalid_client_mapping",
            f"Tenant {tenant_id} client_id mapping mismatch",
        )

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
