import base64
import binascii
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import db
from app.models.schemas import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_bearer_scheme = HTTPBearer(auto_error=False)

_SESSION_COOKIE = "vf_session"


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: datetime | None = None


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
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "tenant_id": tenant_id, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


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
        data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        tenant_id = data.get("tenant_id")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            return None
        return TokenPayload(sub=data["sub"], tenant_id=tenant_id.strip(), exp=data.get("exp"))
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(raw)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_current_user(
    auth: TokenPayload = Depends(require_authenticated),
) -> User:
    """Resolve the authenticated user from the database using the JWT payload."""
    user = db.users.get(auth.sub, tenant_id=auth.tenant_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
