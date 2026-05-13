from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from value_fabric.shared.identity.context import RequestContext
from value_fabric.shared.identity.permissions import Permission, Role
from value_fabric.shared.identity.policy_registry import authorize_action


def test_authorize_action_rejects_missing_scope() -> None:
    context = RequestContext(
        tenant_id="tenant-a",
        user_id="user-1",
        roles=[Role.READ_ONLY.value],
        permissions=frozenset({Permission.READ_SEARCH}),
        auth_source="jwt_claim",
    )

    with pytest.raises(HTTPException) as exc_info:
        authorize_action("layer4.tools.invoke", context)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail["code"] == "INSUFFICIENT_SCOPE"
    assert exc_info.value.detail["action"] == "layer4.tools.invoke"


def test_authorize_action_allows_required_scope() -> None:
    context = RequestContext(
        tenant_id="tenant-a",
        user_id="user-1",
        roles=[Role.ANALYST.value],
        permissions=frozenset({Permission.READ_AGENTS, Permission.WRITE_AGENTS}),
        auth_source="jwt_claim",
    )

    resolved = authorize_action("layer4.tools.invoke", context)

    assert resolved is context


def test_authorize_action_rejects_cross_tenant_after_scope_check() -> None:
    context = RequestContext(
        tenant_id="tenant-a",
        user_id="user-1",
        roles=[Role.CONTENT_ADMIN.value],
        permissions=frozenset({Permission.WRITE_ANALYTICS}),
        auth_source="jwt_claim",
    )

    with pytest.raises(HTTPException) as exc_info:
        authorize_action("layer5.truths.delete", context, target_tenant_id="tenant-b")

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail["code"] == "TENANT_SCOPE_MISMATCH"
