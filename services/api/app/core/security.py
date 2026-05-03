from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_bearer_scheme = HTTPBearer(auto_error=False)

_SESSION_COOKIE = "vf_session"


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    exp: Optional[datetime] = None


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, tenant_id: str, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "tenant_id": tenant_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class TokenExpiredError(ValueError):
    """Raised when a JWT has expired. Translated to HTTP 401 by require_authenticated."""


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT.

    Returns a TokenPayload on success, None for invalid/malformed tokens.
    Raises TokenExpiredError for expired tokens so callers can surface a
    distinct error message without coupling this function to HTTP concerns.
    """
    settings = get_settings()
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return TokenPayload(sub=data["sub"], tenant_id=data.get("tenant_id", "default"), exp=data.get("exp"))
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except JWTError:
        return None


def _extract_token(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials],
    cookie: Optional[str],
) -> Optional[str]:
    """Return the raw JWT from Bearer header or session cookie, in that order."""
    if bearer and bearer.credentials:
        return bearer.credentials
    if cookie:
        return cookie
    return None


def require_authenticated(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    vf_session: Optional[str] = Cookie(default=None, alias=_SESSION_COOKIE),
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
