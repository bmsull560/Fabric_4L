from __future__ import annotations

from uuid import uuid4

import pytest

from canonical.context import (
    AUTH_SOURCE_API_KEY,
    AUTH_SOURCE_UNKNOWN,
    ContextContractError,
    RequestContext,
    clear_current_context,
    get_current_context,
    require_context,
    set_current_context,
)


def test_current_context_roundtrip_and_clear() -> None:
    context = RequestContext(tenant_id=uuid4(), request_id="req-123")

    set_current_context(context)
    assert get_current_context() == context
    assert require_context() == context

    clear_current_context()
    assert get_current_context() is None


def test_require_context_fails_with_actionable_message() -> None:
    clear_current_context()

    with pytest.raises(
        ContextContractError,
        match="No RequestContext is set - ensure GovernanceMiddleware is installed",
    ):
        require_context()


def test_context_to_dict_serializes_uuid_fields() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    api_key_id = uuid4()
    org_id = uuid4()
    service_account_id = uuid4()
    context = RequestContext(
        tenant_id=tenant_id,
        user_id=user_id,
        api_key_id=api_key_id,
        roles=["tenant_admin"],
        permissions=["accounts:read"],
        request_id="req-abc",
        org_id=org_id,
        tenant_role="owner",
        auth_source=AUTH_SOURCE_API_KEY,
        service_account_id=service_account_id,
        service_account_scopes=["agents:run"],
    )

    assert context.to_dict() == {
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "api_key_id": str(api_key_id),
        "roles": ["tenant_admin"],
        "permissions": ["accounts:read"],
        "request_id": "req-abc",
        "org_id": str(org_id),
        "tenant_role": "owner",
        "isolation_tier": "shared",
        "auth_source": AUTH_SOURCE_API_KEY,
        "service_account_id": str(service_account_id),
        "service_account_scopes": ["agents:run"],
    }


def test_context_validation_accepts_valid_values() -> None:
    context = RequestContext(
        tenant_id=uuid4(),
        auth_source=AUTH_SOURCE_API_KEY,
        service_account_id=uuid4(),
        service_account_scopes=["contracts:read"],
    )

    assert context.is_isolation_tier_valid() is True
    assert context.is_auth_source_valid() is True
    assert context.validate() == []


def test_context_validation_reports_invalid_isolation_tier() -> None:
    context = RequestContext(isolation_tier="bogus")

    assert context.is_isolation_tier_valid() is False
    assert context.validate() == ["Invalid isolation_tier: bogus"]


def test_context_validation_reports_invalid_auth_source() -> None:
    context = RequestContext(auth_source="magic-cookie")

    assert context.is_auth_source_valid() is False
    assert context.validate() == ["Invalid auth_source: magic-cookie"]


def test_context_validation_requires_service_account_scopes() -> None:
    context = RequestContext(
        service_account_id=uuid4(),
        service_account_scopes=[],
        auth_source=AUTH_SOURCE_UNKNOWN,
    )

    assert context.validate() == ["Service account must have scopes"]
