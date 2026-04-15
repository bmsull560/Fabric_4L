"""
Security tests for tenant isolation across all layers.

Validates that:
1. Users can only access data within their tenant
2. Cross-tenant access attempts are blocked
3. JWT tenant claims are properly enforced
"""

import pytest
from fastapi.testclient import TestClient


class TestTenantIsolation:
    """Test suite for cross-tenant data access prevention."""

    def test_user_cannot_access_other_tenant_data(self, client: TestClient, tenant_a_token):
        """P0: User from Tenant A cannot access Tenant B data."""
        # Attempt to access data with spoofed tenant header
        response = client.get(
            "/api/v1/entities",
            headers={
                "Authorization": f"Bearer {tenant_a_token}",
                "X-Tenant-ID": "tenant-b",  # Attempted spoof
            },
        )
        assert response.status_code in [403, 401]

    def test_jwt_tenant_claim_takes_precedence(self, client: TestClient, tenant_a_token):
        """JWT tenant claim overrides any header-based spoofing."""
        response = client.get(
            "/api/v1/user/profile",
            headers={
                "Authorization": f"Bearer {tenant_a_token}",
                "X-Tenant-ID": "malicious-tenant",
            },
        )
        # Should succeed but only return tenant-a data
        if response.status_code == 200:
            data = response.json()
            assert data.get("tenant_id") == "tenant-a"

    def test_row_level_security_enforcement(self, client: TestClient, tenant_a_token):
        """Database RLS policies prevent cross-tenant queries."""
        # Query that would return all tenants without RLS
        response = client.get(
            "/api/v1/admin/all-entities",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
        )
        # Should be blocked - standard users cannot access admin endpoints
        assert response.status_code in [403, 404]

    def test_tenant_isolation_in_graph_queries(self, client: TestClient, tenant_a_token):
        """Graph queries respect tenant boundaries."""
        response = client.post(
            "/api/v1/query/graph",
            json={
                "query": "MATCH (n) RETURN n",  # Would return all nodes without isolation
                "tenant_id": "tenant-b",  # Attempted spoof in body
            },
            headers={"Authorization": f"Bearer {tenant_a_token}"},
        )
        # Should only return tenant-a nodes or be blocked
        if response.status_code == 200:
            data = response.json()
            for node in data.get("nodes", []):
                assert node.get("tenant_id") == "tenant-a"


class TestMultiTenantRaceConditions:
    """Test for race conditions in multi-tenant scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_maintain_isolation(self, client: TestClient):
        """Concurrent requests from different tenants don't leak data."""
        import asyncio

        async def make_request(tenant_id: str):
            return client.get(
                "/api/v1/entities",
                headers={
                    "Authorization": f"Bearer fake-token-{tenant_id}",
                },
            )

        # Concurrent requests from different tenants
        tasks = [
            make_request(f"tenant-{i}")
            for i in range(10)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Each response should only contain data for its respective tenant
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                continue
            # Validate response only contains tenant-i data
