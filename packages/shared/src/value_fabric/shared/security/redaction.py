"""Credential redaction helpers for logs and dependency-error messages.

The helpers in this module are intentionally small and dependency-free so they can
be used from any Fabric layer without crossing layer-specific API boundaries.
They are suitable for defensive rendering of exception messages before those
messages are logged, exposed through health details, or asserted by release gates.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SECRET_VALUE = "[REDACTED]"
_SECRET_QUERY_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "auth",
    "authorization",
    "client_secret",
    "key",
    "password",
    "secret",
    "token",
}
_TOKEN_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9._-]{8,}\b"),
    re.compile(r"\b(?:Bearer|Token)\s+[A-Za-z0-9._~+/=-]{8,}\b", re.IGNORECASE),
]
_URL_PATTERN = re.compile(r"https?://[^\s)\]}>\"']+")


def redact_credentials(message: object) -> str:
    """Return ``message`` with obvious credentials redacted.

    The function preserves enough operational context for debugging, including
    host names and non-sensitive path segments, while removing query parameters
    and token-shaped substrings that commonly carry credentials.
    """

    rendered = str(message)
    rendered = _URL_PATTERN.sub(_redact_url_match, rendered)
    for pattern in _TOKEN_PATTERNS:
        rendered = pattern.sub(_SECRET_VALUE, rendered)
    return rendered


def _redact_url_match(match: re.Match[str]) -> str:
    return _redact_url(match.group(0))


def _redact_url(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return url

    if not parts.query:
        return url

    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in _SECRET_QUERY_KEYS:
            query.append((key, _SECRET_VALUE))
        else:
            query.append((key, value))

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


__all__ = ["redact_credentials"]
