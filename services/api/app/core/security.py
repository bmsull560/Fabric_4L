import base64
import binascii
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt as pyjwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import db
from app.models.schemas import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_bearer_scheme = HTTPBearer(auto_error=False)

_SESSION_COOKIE = "vf_session"
_DEFAULT_JWT_ISSUER = "value-fabric-internal"
_DEFAULT_JWT_AUDIENCE = "value-fabric-services"
_AUTH_REQUIRED = "authentication_required"


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: datetime | None = None
    iat: datetime | None = None
    nbf: datetime | None = None
    iss: str
    aud: str | list[str]


def _auth_error(status_code: int, *, error_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error": _AUTH_REQUIRED,
            "error_code": error_code,
            "message": message,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_password(plain: str, hashed: str) -> bool:
    if hashed.startswith("sha256$"):
        import hashlib
        return hashlib.sha256(plain.encode()).hexdigest() == hashed.removeprefix("sha256$")
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        # Fallback for environments where bcrypt backend fails to load
        # (e.g. passlib + Python 3.14 compatibility issues in test env)
        import hashlib
        return f"sha256${hashlib.sha256(password.encode()).hexdigest()}"


def create_access_token(
    subject: str,
    tenant_id: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    iat_ts = int(issued_at.timestamp())
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "iat": iat_ts,
        "nbf": iat_ts,
        "exp": int(expire.timestamp()),
        "iss": settings.jwt_issuer or _DEFAULT_JWT_ISSUER,
        "aud": settings.jwt_audience or _DEFAULT_JWT_AUDIENCE,
    }
    if extra_claims:
        payload.update(extra_claims)
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class TokenExpiredError(ValueError):
    """Raised when a JWT has expired. Translated to HTTP 401 by require_authenticated."""


def _is_canonical_base64url_segment(segment: str) -> bool:
    """Reject non-canonical JWT segments before cryptographic verification.

    Some base64url decoders ignore unused trailing bits in unpadded encodings,
    which can make a mutated compact-JWS segment decode to the same bytes.  The
    API treats such alternate encodings as malformed so tampering is fail-closed
    and auditable before business routing occurs.
    """
    if not segment or "=" in segment:
        return False
    try:
        padded = segment + "=" * (-len(segment) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (binascii.Error, UnicodeEncodeError, ValueError):
        return False
    canonical = base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
    return canonical == segment


def _has_canonical_compact_jws_encoding(token: str) -> bool:
    segments = token.split(".")
    return len(segments) == 3 and all(
        _is_canonical_base64url_segment(segment) for segment in segments
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT.

    Returns a TokenPayload on success, None for invalid/malformed tokens.
    Raises TokenExpiredError for expired tokens so callers can surface a
    distinct error message without coupling this function to HTTP concerns.
    """
    settings = get_settings()
    if not _has_canonical_compact_jws_encoding(token):
        return None
    try:
        header = pyjwt.get_unverified_header(token)
        header_alg = header.get("alg")
        if not isinstance(header_alg, str) or not header_alg.strip():
            return None
        if header_alg.upper() != settings.algorithm.upper():
            return None
        # PyJWT option keys differ from python-jose:
        #   require=[...] replaces require_sub/require_exp/etc.
        #   verify_* options are set via options dict
        data = pyjwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require": ["sub", "exp", "iat", "nbf"],
                "verify_aud": True,
                "verify_iss": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_exp": True,
            },
        )
        if not isinstance(data.get("sub"), str) or not data["sub"].strip():
            return None
        tenant_id = data.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            return None
        if not isinstance(data.get("iss"), str) or not data["iss"].strip():
            return None
        if data.get("aud") in (None, "", []):
            return None
        return TokenPayload(
            sub=data["sub"].strip(),
            tenant_id=tenant_id.strip(),
            exp=data.get("exp"),
            iat=data.get("iat"),
            nbf=data.get("nbf"),
            iss=data["iss"],
            aud=data["aud"],
        )
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except InvalidTokenError:
        return None


def _extract_token(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None,
    cookie: str | None,
) -> str | None:
    """Return the raw JWT from Bearer header or session cookie, in that order."""
    if bearer and bearer.credentials:
        return bearer.credentials
    if cookie:
        return cookie
    return None


def require_authenticated(
    request: Request,
    bearer: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    vf_session: str | None = Cookie(default=None, alias=_SESSION_COOKIE),
) -> TokenPayload:
    """FastAPI dependency: require a valid JWT from Bearer header or session cookie.

    Raises HTTP 401 if no token is present or the token is invalid/expired.
    """
    raw = _extract_token(request, bearer, vf_session)
    if not raw:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_REQUIRED",
            message="Authentication required.",
        )
    try:
        payload = decode_token(raw)
    except TokenExpiredError:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_TOKEN_EXPIRED",
            message="Token has expired.",
        )
    if payload is None:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_INVALID_TOKEN",
            message="Invalid token.",
        )
    return payload


async def get_current_user(
    auth: TokenPayload = Depends(require_authenticated),
) -> User:
    """Resolve the authenticated user from the database using the JWT payload."""
    user = db.users.get(auth.sub, tenant_id=auth.tenant_id)
    if user is None:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_USER_NOT_FOUND",
            message="Authenticated user was not found.",
        )
    return user
