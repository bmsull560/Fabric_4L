"""
Test tier-aware isolation invariants.

Verifies that unimplemented tiers (schema, database) return HTTP 501
and only the shared tier is currently functional.

Critical P0 test - tier misconfiguration could cause HTTP 501 errors.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from uuid import uuid4

from services.layer4_agents.src.database import (
    get_tiered_db_session,
    ISOLATION_TIER_SHARED,
    ISOLATION_TIER_SCHEMA,
    ISOLATION_TIER_DATABASE,
)
from services.layer4_agents.src.database import TenantContextError


class TestTierAwareIsolation:
    """Test suite for tier-aware isolation invariants."""

    @pytest.mark.asyncio
    async def test_shared_tier_is_functional(self):
        """
        POSITIVE: Shared tier should be functional.
        Tests the default and currently implemented tier.
        """
        tenant_id = str(uuid4())
        context = Mock()
        context.tenant_id = tenant_id
        context.isolation_tier = ISOLATION_TIER_SHARED

        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value().__aenter__.return_value = mock_session

            session_generator = get_tiered_db_session(context)
            session = await session_generator.__anext__()

            assert session is not None

    @pytest.mark.asyncio
    async def test_schema_tier_returns_501(self):
        """
        NEGATIVE: Schema tier should return HTTP 501 (Not Implemented).
        Tests that unimplemented tiers are properly rejected.
        """
        tenant_id = str(uuid4())
        context = Mock()
        context.tenant_id = tenant_id
        context.isolation_tier = ISOLATION_TIER_SCHEMA

        with pytest.raises(HTTPException) as exc_info:
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()

        assert exc_info.value.status_code == 501
        assert "not implemented" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_database_tier_returns_501(self):
        """
        NEGATIVE: Database tier should return HTTP 501 (Not Implemented).
        Tests that unimplemented tiers are properly rejected.
        """
        tenant_id = str(uuid4())
        context = Mock()
        context.tenant_id = tenant_id
        context.isolation_tier = ISOLATION_TIER_DATABASE

        with pytest.raises(HTTPException) as exc_info:
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()

        assert exc_info.value.status_code == 501
        assert "not implemented" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_invalid_tier_returns_501(self):
        """
        NEGATIVE: Invalid tier should return HTTP 501 (Not Implemented).
        Tests that invalid tier configurations are rejected.
        """
        tenant_id = str(uuid4())
        context = Mock()
        context.tenant_id = tenant_id
        context.isolation_tier = "invalid_tier"

        with pytest.raises(HTTPException) as exc_info:
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()

        assert exc_info.value.status_code == 501

    @pytest.mark.asyncio
    async def test_tier_validation_in_context(self):
        """
        POSITIVE: Tier should be validated in RequestContext.
        Tests that valid tiers are accepted.
        """
        from value_fabric.shared.identity.context import RequestContext, VALID_ISOLATION_TIERS

        for tier in VALID_ISOLATION_TIERS:
            context = RequestContext(
                tenant_id=str(uuid4()),
                user_id="user123",
                isolation_tier=tier,
            )
            assert context.isolation_tier == tier

    def test_default_tier_is_shared(self):
        """
        POSITIVE: Default tier should be 'shared'.
        Tests that the default configuration is correct.
        """
        from value_fabric.shared.identity.context import RequestContext, ISOLATION_TIER_SHARED

        context = RequestContext(tenant_id=str(uuid4()), user_id="user123")

        assert context.isolation_tier == ISOLATION_TIER_SHARED

    @pytest.mark.asyncio
    async def test_tier_transition_from_shared_to_schema_fails(self):
        """
        NEGATIVE: Transitioning from shared to schema tier should fail with 501.
        Tests that tier transitions to unimplemented tiers are blocked.
        """
        tenant_id = str(uuid4())
        context = Mock()
        context.tenant_id = tenant_id
        context.isolation_tier = ISOLATION_TIER_SHARED

        # Start with shared tier (should work)
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value().__aenter__.return_value = mock_session

            session_generator = get_tiered_db_session(context)
            session = await session_generator.__anext__()
            assert session is not None

        # Try to switch to schema tier (should fail)
        context.isolation_tier = ISOLATION_TIER_SCHEMA

        with pytest.raises(HTTPException) as exc_info:
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()

        assert exc_info.value.status_code == 501


class TestIsolationTierValidation:
    """Test suite for isolation tier validation invariants."""

    def test_valid_isolation_tiers(self):
        """
        POSITIVE: Valid isolation tiers should be defined.
        Tests that the tier constants are properly defined.
        """
        from services.layer4_agents.src.database import (
            ISOLATION_TIER_SHARED,
            ISOLATION_TIER_SCHEMA,
            ISOLATION_TIER_DATABASE,
        )

        assert ISOLATION_TIER_SHARED == "shared"
        assert ISOLATION_TIER_SCHEMA == "schema"
        assert ISOLATION_TIER_DATABASE == "database"

    def test_tier_constants_are_unique(self):
        """
        POSITIVE: Tier constants should be unique.
        Tests that there are no duplicate tier values.
        """
        from services.layer4_agents.src.database import (
            ISOLATION_TIER_SHARED,
            ISOLATION_TIER_SCHEMA,
            ISOLATION_TIER_DATABASE,
        )

        tiers = [ISOLATION_TIER_SHARED, ISOLATION_TIER_SCHEMA, ISOLATION_TIER_DATABASE]
        assert len(tiers) == len(set(tiers))

    def test_shared_tier_is_string(self):
        """
        POSITIVE: Shared tier should be a string.
        Tests type correctness.
        """
        from services.layer4_agents.src.database import ISOLATION_TIER_SHARED

        assert isinstance(ISOLATION_TIER_SHARED, str)

    def test_schema_tier_is_string(self):
        """
        POSITIVE: Schema tier should be a string.
        Tests type correctness.
        """
        from services.layer4_agents.src.database import ISOLATION_TIER_SCHEMA

        assert isinstance(ISOLATION_TIER_SCHEMA, str)

    def test_database_tier_is_string(self):
        """
        POSITIVE: Database tier should be a string.
        Tests type correctness.
        """
        from services.layer4_agents.src.database import ISOLATION_TIER_DATABASE

        assert isinstance(ISOLATION_TIER_DATABASE, str)


class TestTierGracefulDegradation:
    """Test suite for tier graceful degradation invariants."""

    @pytest.mark.asyncio
    async def test_shared_tier_handles_missing_tenant_id(self):
        """
        NEGATIVE: Shared tier should handle missing tenant_id with appropriate error.
        Tests fail-safe behavior.
        """
        context = Mock()
        context.tenant_id = None
        context.isolation_tier = ISOLATION_TIER_SHARED

        with pytest.raises((HTTPException, TenantContextError)):
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()

    @pytest.mark.asyncio
    async def test_shared_tier_handles_invalid_tenant_id(self):
        """
        NEGATIVE: Shared tier should handle invalid tenant_id with appropriate error.
        Tests UUID validation.
        """
        context = Mock()
        context.tenant_id = "not-a-uuid"
        context.isolation_tier = ISOLATION_TIER_SHARED

        with pytest.raises((HTTPException, TenantContextError)):
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()

    @pytest.mark.asyncio
    async def test_shared_tier_handles_empty_tenant_id(self):
        """
        NEGATIVE: Shared tier should handle empty tenant_id with appropriate error.
        Tests empty string validation.
        """
        context = Mock()
        context.tenant_id = ""
        context.isolation_tier = ISOLATION_TIER_SHARED

        with pytest.raises((HTTPException, TenantContextError)):
            session_generator = get_tiered_db_session(context)
            await session_generator.__anext__()
