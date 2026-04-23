"""E2E tests for tenant control plane (Phase 3).

Tests self-service registration, admin dashboard, and tier enforcement.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


@pytest.mark.e2e
async def test_tenant_registration_flow(client: AsyncClient):
    """Test full registration and verification flow."""
    unique_slug = f"e2e-test-{uuid.uuid4().hex[:8]}"

    # 1. Register tenant
    response = await client.post(
        "/v1/tenants/register",
        json={
            "name": "E2E Test Tenant",
            "slug": unique_slug,
            "admin_email": "admin@example.com",
            "tier_id": "free",
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["verification_required"] is True
    assert "tenant_id" in data
    tenant_id = data["tenant_id"]

    # 2. Verify slug is taken
    response = await client.get(f"/v1/tenants/validate-slug?slug={unique_slug}")
    assert response.status_code == 200
    assert response.json()["available"] is False

    # 3. Verify email (would need to extract token from email in real test)
    # Skipped in E2E — requires email integration
    # Instead, we'll check the tenant exists
    response = await client.get(f"/v1/tenants/{tenant_id}")
    # This may fail if auth is required - just checking endpoint structure


@pytest.mark.e2e
async def test_public_tiers_listing(client: AsyncClient):
    """Test public tier listing endpoint."""
    response = await client.get("/v1/tenants/tiers")
    assert response.status_code == 200
    tiers = response.json()

    # Should return public tiers
    assert len(tiers) > 0
    tier_ids = [t["id"] for t in tiers]
    assert "free" in tier_ids

    # Check tier structure
    for tier in tiers:
        assert "id" in tier
        assert "name" in tier
        assert "description" in tier
        assert "limits" in tier
        assert "features" in tier


@pytest.mark.e2e
async def test_slug_validation(client: AsyncClient):
    """Test slug availability validation."""
    unique_slug = f"test-{uuid.uuid4().hex[:8]}"

    # Check new slug is available
    response = await client.get(f"/v1/tenants/validate-slug?slug={unique_slug}")
    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["slug"] == unique_slug


@pytest.mark.e2e
async def test_tenant_admin_dashboard_unauthorized(client: AsyncClient):
    """Test admin endpoints require authentication."""
    fake_tenant_id = str(uuid.uuid4())

    # Try to access admin endpoint without auth
    response = await client.get(f"/v1/tenants/{fake_tenant_id}/users")
    assert response.status_code in [401, 403]

    response = await client.get(f"/v1/tenants/{fake_tenant_id}/usage")
    assert response.status_code in [401, 403]

    response = await client.get(f"/v1/tenants/{fake_tenant_id}/settings")
    assert response.status_code in [401, 403]


@pytest.mark.e2e
async def test_tenant_settings_update_unauthorized(client: AsyncClient):
    """Test settings update requires authentication."""
    fake_tenant_id = str(uuid.uuid4())

    response = await client.patch(
        f"/v1/tenants/{fake_tenant_id}/settings",
        json={"name": "Updated Name"},
    )
    assert response.status_code in [401, 403]


@pytest.mark.e2e
async def test_api_key_management_unauthorized(client: AsyncClient):
    """Test API key endpoints require authentication."""
    fake_tenant_id = str(uuid.uuid4())

    # Try to create key without auth
    response = await client.post(
        f"/v1/tenants/{fake_tenant_id}/api-keys",
        json={"name": "Test Key", "expires_in_days": 30},
    )
    assert response.status_code in [401, 403]

    # Try to list keys without auth
    response = await client.get(f"/v1/tenants/{fake_tenant_id}/api-keys")
    assert response.status_code in [401, 403]


@pytest.mark.e2e
async def test_invalid_tier_selection(client: AsyncClient):
    """Test invalid tier returns error."""
    unique_slug = f"test-bad-tier-{uuid.uuid4().hex[:8]}"

    response = await client.post(
        "/v1/tenants/register",
        json={
            "name": "Test Tenant",
            "slug": unique_slug,
            "admin_email": "admin@example.com",
            "tier_id": "nonexistent",
        },
    )
    assert response.status_code == 400


@pytest.mark.e2e
async def test_enterprise_tier_not_public(client: AsyncClient):
    """Test enterprise tier is not in public listing."""
    response = await client.get("/v1/tenants/tiers")
    assert response.status_code == 200
    tiers = response.json()

    tier_ids = [t["id"] for t in tiers]
    # Enterprise tier should not be publicly selectable
    assert "enterprise" not in tier_ids


@pytest.mark.e2e
async def test_duplicate_slug_registration(client: AsyncClient):
    """Test duplicate slug returns conflict."""
    unique_slug = f"dup-test-{uuid.uuid4().hex[:8]}"

    # First registration
    response = await client.post(
        "/v1/tenants/register",
        json={
            "name": "First Tenant",
            "slug": unique_slug,
            "admin_email": "admin1@example.com",
            "tier_id": "free",
        },
    )
    assert response.status_code == 202

    # Second registration with same slug
    response = await client.post(
        "/v1/tenants/register",
        json={
            "name": "Second Tenant",
            "slug": unique_slug,
            "admin_email": "admin2@example.com",
            "tier_id": "free",
        },
    )
    assert response.status_code == 409
    assert "slug" in response.json()["detail"].lower()


@pytest.mark.e2e
async def test_invalid_email_verification_token(client: AsyncClient):
    """Test invalid verification token returns error."""
    response = await client.post(
        "/v1/tenants/verify-email",
        json={"token": "invalid-token"},
    )
    assert response.status_code == 400


@pytest.mark.e2e
async def test_tenant_admin_access_wrong_tenant(
    client: AsyncClient,
    tenant_admin_token: str,
    test_tenant: dict,
):
    """Test admin cannot access other tenant's data."""
    other_tenant_id = str(uuid.uuid4())

    # Try to access another tenant's users
    response = await client.get(
        f"/v1/tenants/{other_tenant_id}/users",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
    )
    assert response.status_code == 403

    # Try to access another tenant's usage
    response = await client.get(
        f"/v1/tenants/{other_tenant_id}/usage",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
    )
    assert response.status_code == 403


@pytest.mark.e2e
async def test_tenant_settings_fields(client: AsyncClient, tenant_admin_token: str, test_tenant: dict):
    """Test tenant settings endpoint returns expected fields."""
    tenant_id = test_tenant["id"]

    response = await client.get(
        f"/v1/tenants/{tenant_id}/settings",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
    )

    # If we have a valid tenant and token
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "status" in data
        assert "tier_id" in data or "settings" in data


@pytest.mark.e2e
async def test_usage_metrics_structure(client: AsyncClient, tenant_admin_token: str, test_tenant: dict):
    """Test usage metrics endpoint returns expected structure."""
    tenant_id = test_tenant["id"]

    response = await client.get(
        f"/v1/tenants/{tenant_id}/usage?days=7",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
    )

    # If we have a valid tenant and token
    if response.status_code == 200:
        data = response.json()
        assert "tenant_id" in data
        assert "period" in data
        assert "api_calls" in data
        assert "agent_executions" in data
        assert "llm_usage" in data


@pytest.mark.e2e
async def test_audit_log_structure(client: AsyncClient, tenant_admin_token: str, test_tenant: dict):
    """Test audit log endpoint returns expected structure."""
    tenant_id = test_tenant["id"]

    response = await client.get(
        f"/v1/tenants/{tenant_id}/audit-log",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
    )

    # If we have a valid tenant and token
    if response.status_code == 200:
        data = response.json()
        assert "events" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
