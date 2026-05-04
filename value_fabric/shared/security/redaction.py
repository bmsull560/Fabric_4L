"""Credential redaction helpers for logs and dependency-error messages.

This compatibility module intentionally mirrors the canonical shared-package
redaction helper so production gates can import the stable
``value_fabric.shared.security.redaction`` path while preserving the same
small, dependency-free behavior used by runtime packages.
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
    """Return ``message`` with obvious credentials redacted."""

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
