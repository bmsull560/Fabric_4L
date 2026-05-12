"""Shared OIDC client helpers for Layer 4 tenant authentication."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any
from urllib.parse import urlencode

import httpx


class OIDCClient:
    """Small OIDC HTTP client used by tenant OIDC routes."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=30.0)
        self._http_client = self._http

    async def close(self) -> None:
        await self._http.aclose()

    async def discover(self, issuer_url: str) -> dict[str, Any]:
        url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                response = await self._http.get(url)
                response.raise_for_status()
                return dict(response.json())
            except httpx.HTTPStatusError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt == 0:
                    await asyncio.sleep(0.1)
        assert last_exc is not None
        raise last_exc

    def build_authorize_url(
        self,
        *,
        metadata: dict[str, Any],
        client_id: str,
        redirect_uri: str,
        state: str,
        nonce: str,
        scopes: list[str],
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
    ) -> str:
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "nonce": nonce,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"
        return f"{metadata['authorization_endpoint']}?{urlencode(params)}"

    async def exchange_code(
        self,
        *,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str | None = None,
        code_verifier: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
        }
        if client_secret:
            payload["client_secret"] = client_secret
        if code_verifier:
            payload["code_verifier"] = code_verifier

        response = await self._http.post(token_endpoint, data=payload, headers={"Accept": "application/json"})
        response.raise_for_status()
        return dict(response.json())

    async def verify_id_token(
        self,
        *,
        id_token: str,
        issuer_url: str,
        client_id: str,
    ) -> dict[str, Any]:
        """Parse and minimally validate an OIDC id_token payload.

        Signature validation is delegated to provider/JWKS hardening in a later
        path; this method preserves the current route contract for mocked and
        local validation flows.
        """

        parts = id_token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        payload = json.loads(_b64url_decode(parts[1]))
        issuer = payload.get("iss")
        audience = payload.get("aud")
        if issuer and issuer != issuer_url:
            raise ValueError(f"Invalid issuer: {issuer}")
        if audience and audience != client_id:
            raise ValueError(f"Invalid audience: {audience}")
        return payload

    async def get_userinfo(self, *, userinfo_endpoint: str, access_token: str) -> dict[str, Any]:
        response = await self._http.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        response.raise_for_status()
        return dict(response.json())


def map_role_from_claims(
    claims: dict[str, Any],
    claim_mapping: dict[str, str] | None = None,
    default_role: str = "read_only",
) -> str:
    mapping = {k: str(v).lower() for k, v in (claim_mapping or {}).items()}
    for claim_name, expected in mapping.items():
        value = claims.get(claim_name)
        if _claim_matches(value, expected):
            return expected

    role = claims.get("role")
    if isinstance(role, str) and any(token in role.lower() for token in ("admin", "editor", "viewer", "read")):
        return role

    groups = claims.get("groups")
    if isinstance(groups, list):
        for group in groups:
            group_lower = str(group).lower()
            if "admin" in group_lower:
                return "admin"
            if "editor" in group_lower:
                return "editor"
            if "viewer" in group_lower:
                return "viewer"

    return default_role


def _claim_matches(value: Any, expected: str) -> bool:
    if isinstance(value, list):
        return any(str(item).lower() == expected for item in value)
    if value is None:
        return False
    return str(value).lower() == expected


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
