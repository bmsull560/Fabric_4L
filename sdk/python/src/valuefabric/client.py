"""Synchronous and asynchronous HTTP clients for Value Fabric."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .auth import APIKeyAuth, Auth, JWTAuth
from .models import (
    APIKey,
    APIKeyCreateResult,
    FeatureFlag,
    HealthResponse,
    ModelVersion,
    Tenant,
    User,
    Workflow,
    WorkflowTypeInfo,
)


class ValueFabricClient:
    """Typed HTTP client for the Value Fabric Layer 4 API.

    Parameters
    ----------
    base_url:
        Root URL of the Layer 4 API (e.g. ``https://api.valuefabric.io``).
    api_key:
        Optional API key. If provided, the ``X-API-Key`` header is sent on every request.
    jwt_token:
        Optional JWT bearer token. Mutually exclusive with ``api_key``.
    timeout:
        Request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        jwt_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        auth: Optional[Auth] = None
        if api_key:
            auth = APIKeyAuth(api_key)
        elif jwt_token:
            auth = JWTAuth(jwt_token)

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self._sync_client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            auth=auth,  # type: ignore[arg-type]
        )
        self._async_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            auth=auth,  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = self._sync_client.request(method, path, params=params, json=json)
        response.raise_for_status()
        return response.json()

    async def _arequest(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        response = await self._async_client.request(method, path, params=params, json=json)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Tenants
    # ------------------------------------------------------------------

    def list_tenants(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Tenant]:
        payload = self._request(
            "GET",
            "/v1/tenants",
            params={"status": status, "limit": limit, "offset": offset},
        )
        return [Tenant.model_validate(item) for item in payload]

    async def alist_tenants(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Tenant]:
        payload = await self._arequest(
            "GET",
            "/v1/tenants",
            params={"status": status, "limit": limit, "offset": offset},
        )
        return [Tenant.model_validate(item) for item in payload]

    def get_tenant(self, tenant_id: str) -> Tenant:
        payload = self._request("GET", f"/v1/tenants/{tenant_id}")
        return Tenant.model_validate(payload)

    async def aget_tenant(self, tenant_id: str) -> Tenant:
        payload = await self._arequest("GET", f"/v1/tenants/{tenant_id}")
        return Tenant.model_validate(payload)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def list_users(self, *, limit: int = 100, offset: int = 0) -> List[User]:
        payload = self._request("GET", "/v1/users", params={"limit": limit, "offset": offset})
        return [User.model_validate(item) for item in payload]

    async def alist_users(self, *, limit: int = 100, offset: int = 0) -> List[User]:
        payload = await self._arequest(
            "GET", "/v1/users", params={"limit": limit, "offset": offset}
        )
        return [User.model_validate(item) for item in payload]

    def invite_user(self, email: str, role: str, *, display_name: Optional[str] = None) -> User:
        payload = self._request(
            "POST",
            "/v1/users/invite",
            json={"email": email, "role": role, "display_name": display_name},
        )
        return User.model_validate(payload)

    async def ainvite_user(
        self, email: str, role: str, *, display_name: Optional[str] = None
    ) -> User:
        payload = await self._arequest(
            "POST",
            "/v1/users/invite",
            json={"email": email, "role": role, "display_name": display_name},
        )
        return User.model_validate(payload)

    # ------------------------------------------------------------------
    # API Keys
    # ------------------------------------------------------------------

    def list_api_keys(self, *, enabled_only: bool = True) -> List[APIKey]:
        payload = self._request("GET", "/v1/api-keys", params={"enabled_only": enabled_only})
        return [APIKey.model_validate(item) for item in payload]

    async def alist_api_keys(self, *, enabled_only: bool = True) -> List[APIKey]:
        payload = await self._arequest(
            "GET", "/v1/api-keys", params={"enabled_only": enabled_only}
        )
        return [APIKey.model_validate(item) for item in payload]

    def create_api_key(
        self,
        name: str,
        role: str,
        *,
        expires_at: Optional[str] = None,
        rate_limit_per_minute: Optional[int] = None,
    ) -> APIKeyCreateResult:
        json_body: Dict[str, Any] = {"name": name, "role": role}
        if expires_at is not None:
            json_body["expires_at"] = expires_at
        if rate_limit_per_minute is not None:
            json_body["rate_limit_per_minute"] = rate_limit_per_minute
        payload = self._request("POST", "/v1/api-keys", json=json_body)
        return APIKeyCreateResult.model_validate(payload)

    async def acreate_api_key(
        self,
        name: str,
        role: str,
        *,
        expires_at: Optional[str] = None,
        rate_limit_per_minute: Optional[int] = None,
    ) -> APIKeyCreateResult:
        json_body: Dict[str, Any] = {"name": name, "role": role}
        if expires_at is not None:
            json_body["expires_at"] = expires_at
        if rate_limit_per_minute is not None:
            json_body["rate_limit_per_minute"] = rate_limit_per_minute
        payload = await self._arequest("POST", "/v1/api-keys", json=json_body)
        return APIKeyCreateResult.model_validate(payload)

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def list_workflows(self) -> List[WorkflowTypeInfo]:
        payload = self._request("GET", "/v1/workflows/types")
        return [WorkflowTypeInfo.model_validate(item) for item in payload.get("workflows", [])]

    async def alist_workflows(self) -> List[WorkflowTypeInfo]:
        payload = await self._arequest("GET", "/v1/workflows/types")
        return [WorkflowTypeInfo.model_validate(item) for item in payload.get("workflows", [])]

    def list_active_workflows(self) -> List[Workflow]:
        payload = self._request("GET", "/v1/workflows/active")
        # The API returns a list of dicts directly.
        return [Workflow.model_validate(item) for item in payload]

    async def alist_active_workflows(self) -> List[Workflow]:
        payload = await self._arequest("GET", "/v1/workflows/active")
        return [Workflow.model_validate(item) for item in payload]

    def execute_workflow(
        self,
        workflow_type: str,
        tenant_id: str,
        user_id: str,
        *,
        inputs: Optional[Dict[str, Any]] = None,
        priority: str = "NORMAL",
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        json_body: Dict[str, Any] = {
            "workflow_type": workflow_type,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "inputs": inputs or {},
            "priority": priority,
        }
        if workflow_id is not None:
            json_body["workflow_id"] = workflow_id
        return self._request("POST", "/v1/workflows", json=json_body)

    async def aexecute_workflow(
        self,
        workflow_type: str,
        tenant_id: str,
        user_id: str,
        *,
        inputs: Optional[Dict[str, Any]] = None,
        priority: str = "NORMAL",
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        json_body: Dict[str, Any] = {
            "workflow_type": workflow_type,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "inputs": inputs or {},
            "priority": priority,
        }
        if workflow_id is not None:
            json_body["workflow_id"] = workflow_id
        return await self._arequest("POST", "/v1/workflows", json=json_body)

    def get_workflow(self, workflow_id: str) -> Workflow:
        payload = self._request("GET", f"/v1/workflows/{workflow_id}")
        return Workflow.model_validate(payload)

    async def aget_workflow(self, workflow_id: str) -> Workflow:
        payload = await self._arequest("GET", f"/v1/workflows/{workflow_id}")
        return Workflow.model_validate(payload)

    # ------------------------------------------------------------------
    # Models (Registry)
    # ------------------------------------------------------------------

    def list_models(self, *, stage: Optional[str] = None) -> List[ModelVersion]:
        params = {"stage": stage} if stage else None
        payload = self._request("GET", "/v1/models", params=params)
        return [ModelVersion.model_validate(item) for item in payload]

    async def alist_models(self, *, stage: Optional[str] = None) -> List[ModelVersion]:
        params = {"stage": stage} if stage else None
        payload = await self._arequest("GET", "/v1/models", params=params)
        return [ModelVersion.model_validate(item) for item in payload]

    def promote_model(
        self, model_id: str, to_stage: str, *, reason: Optional[str] = None
    ) -> ModelVersion:
        payload = self._request(
            "POST",
            f"/v1/models/{model_id}/promote",
            json={"to_stage": to_stage, "reason": reason},
        )
        return ModelVersion.model_validate(payload)

    async def apromote_model(
        self, model_id: str, to_stage: str, *, reason: Optional[str] = None
    ) -> ModelVersion:
        payload = await self._arequest(
            "POST",
            f"/v1/models/{model_id}/promote",
            json={"to_stage": to_stage, "reason": reason},
        )
        return ModelVersion.model_validate(payload)

    # ------------------------------------------------------------------
    # Feature Flags
    # ------------------------------------------------------------------

    def list_feature_flags(
        self, *, limit: int = 100, offset: int = 0
    ) -> List[FeatureFlag]:
        payload = self._request(
            "GET",
            "/v1/feature-flags",
            params={"limit": limit, "offset": offset},
        )
        return [FeatureFlag.model_validate(item) for item in payload]

    async def alist_feature_flags(
        self, *, limit: int = 100, offset: int = 0
    ) -> List[FeatureFlag]:
        payload = await self._arequest(
            "GET",
            "/v1/feature-flags",
            params={"limit": limit, "offset": offset},
        )
        return [FeatureFlag.model_validate(item) for item in payload]

    def set_feature_flag(
        self,
        key: str,
        enabled: bool,
        *,
        rollout_percentage: int = 100,
        description: Optional[str] = None,
    ) -> FeatureFlag:
        json_body: Dict[str, Any] = {
            "enabled": enabled,
            "rollout_percentage": rollout_percentage,
        }
        if description is not None:
            json_body["description"] = description
        payload = self._request("PUT", f"/v1/feature-flags/{key}", json=json_body)
        return FeatureFlag.model_validate(payload)

    async def aset_feature_flag(
        self,
        key: str,
        enabled: bool,
        *,
        rollout_percentage: int = 100,
        description: Optional[str] = None,
    ) -> FeatureFlag:
        json_body: Dict[str, Any] = {
            "enabled": enabled,
            "rollout_percentage": rollout_percentage,
        }
        if description is not None:
            json_body["description"] = description
        payload = await self._arequest("PUT", f"/v1/feature-flags/{key}", json=json_body)
        return FeatureFlag.model_validate(payload)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> HealthResponse:
        payload = self._request("GET", "/health")
        return HealthResponse.model_validate(payload)

    async def ahealth(self) -> HealthResponse:
        payload = await self._arequest("GET", "/health")
        return HealthResponse.model_validate(payload)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._sync_client.close()

    async def aclose(self) -> None:
        await self._async_client.aclose()

    def __enter__(self) -> "ValueFabricClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    async def __aenter__(self) -> "ValueFabricClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
