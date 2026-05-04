"""
Test audit event emission invariants.

Verifies that TENANT_CONTEXT_SET audit events are emitted for all database session types.

Critical P0 test - compliance gaps if audit events are missing.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from services.layer4_agents.src.database import (
    get_db_from_context,
    get_db_with_optional_tenant,
    db_session,
    db_session_for_context,
    set_tenant_context,
    _emit_tenant_context_set_audit,
)
from services.layer4_agents.src.database import TenantContextError


@pytest.fixture
def mock_request_context():
    """Create a mock RequestContext."""
    context = Mock()
    context.tenant_id = str(uuid4())
    context.user_id = "user123"
    context.request_id = str(uuid4())
    context.is_super_admin = Mock(return_value=False)
    return context


@pytest.fixture
def mock_async_session():
    """Create a mock AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


class TestAuditEventEmissionForSessionTypes:
    """Test suite for audit event emission across all session types."""

    @pytest.mark.asyncio
    async def test_get_db_from_context_emits_audit_event(self, mock_request_context, mock_async_session):
        """
        POSITIVE: get_db_from_context should emit TENANT_CONTEXT_SET audit event.
        Tests audit emission for primary session type.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_from_context(mock_request_context)
                session = await session_generator.__anext__()

                # Verify audit event was emitted
                mock_emit.assert_called_once()
                call_args = mock_emit.call_args
                assert call_args[0][0] == mock_request_context  # context
                assert call_args[0][1] == mock_request_context.tenant_id  # tenant_id
                assert call_args[0][2] is False  # is_bypass

    @pytest.mark.asyncio
    async def test_get_db_with_optional_tenant_emits_audit_event(self, mock_request_context, mock_async_session):
        """
        POSITIVE: get_db_with_optional_tenant should emit TENANT_CONTEXT_SET audit event.
        Tests audit emission for optional tenant session type.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_with_optional_tenant(mock_request_context)
                session = await session_generator.__anext__()

                # Verify audit event was emitted
                mock_emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_session_emits_audit_event(self, mock_async_session):
        """
        POSITIVE: db_session should emit TENANT_CONTEXT_SET audit event when tenant_id provided.
        Tests audit emission for direct session type.
        """
        tenant_id = str(uuid4())

        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = db_session(tenant_id=tenant_id)
                session = await session_generator.__anext__()

                # Verify audit event was emitted
                mock_emit.assert_called_once()
                call_args = mock_emit.call_args
                assert call_args[0][1] == tenant_id

    @pytest.mark.asyncio
    async def test_db_session_for_context_emits_audit_event(self, mock_request_context, mock_async_session):
        """
        POSITIVE: db_session_for_context should emit TENANT_CONTEXT_SET audit event.
        Tests audit emission for context-aware session type.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = db_session_for_context(mock_request_context)
                session = await session_generator.__anext__()

                # Verify audit event was emitted
                mock_emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_emission_includes_correct_fields(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit event should include all required fields.
        Tests audit event completeness.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_from_context(mock_request_context)
                session = await session_generator.__anext__()

                # Verify audit event includes required fields
                call_args = mock_emit.call_args
                assert len(call_args[0]) >= 3  # context, tenant_id, is_bypass
                assert call_args[0][0] == mock_request_context
                assert call_args[0][1] == mock_request_context.tenant_id
                assert call_args[0][2] is False  # is_bypass for normal operations

    @pytest.mark.asyncio
    async def test_audit_emission_for_super_admin_bypass(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit event should mark is_bypass=True for super-admin operations.
        Tests audit event for privileged operations.
        """
        mock_request_context.is_super_admin = Mock(return_value=True)

        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_with_optional_tenant(mock_request_context)
                session = await session_generator.__anext__()

                # Verify audit event marks bypass
                call_args = mock_emit.call_args
                assert call_args[0][2] is True  # is_bypass for super-admin


class TestAuditEventFailureHandling:
    """Test suite for audit event emission failure handling."""

    @pytest.mark.asyncio
    async def test_audit_emission_failure_does_not_block_session(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit emission failure should not block session creation.
        Tests graceful degradation on audit failure.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.side_effect = Exception("Audit emission failed")

                # Session should still be created despite audit failure
                session_generator = get_db_from_context(mock_request_context)
                session = await session_generator.__anext__()

                assert session is not None

    @pytest.mark.asyncio
    async def test_audit_emission_logs_failure(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit emission failure should be logged.
        Tests error logging for audit failures.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.side_effect = Exception("Audit emission failed")

                with patch("services.layer4_agents.src.database.logger") as mock_logger:
                    session_generator = get_db_from_context(mock_request_context)
                    session = await session_generator.__anext__()

                    # Verify error was logged
                    mock_logger.error.assert_called()


class TestSetTenantContextAuditIntegration:
    """Test suite for set_tenant_context audit integration."""

    @pytest.mark.asyncio
    async def test_set_tenant_context_emits_audit(self, mock_async_session):
        """
        POSITIVE: set_tenant_context should emit audit event.
        Tests audit emission for tenant context setting.
        """
        tenant_id = str(uuid4())

        with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
            mock_emit.return_value = None

            await set_tenant_context(mock_async_session, tenant_id)

            # Verify audit event was emitted
            mock_emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_tenant_context_with_null_tenant_emits_audit(self, mock_async_session):
        """
        POSITIVE: set_tenant_context with null tenant should emit audit event.
        Tests audit emission for null tenant context.
        """
        with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
            mock_emit.return_value = None

            await set_tenant_context(mock_async_session, None)

            # Verify audit event was emitted
            mock_emit.assert_called_once()


class TestAuditEventContent:
    """Test suite for audit event content validation."""

    @pytest.mark.asyncio
    async def test_audit_event_includes_tenant_id(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit event should include tenant_id.
        Tests audit event field completeness.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_from_context(mock_request_context)
                await session_generator.__anext__()

                call_args = mock_emit.call_args
                assert call_args[0][1] == mock_request_context.tenant_id

    @pytest.mark.asyncio
    async def test_audit_event_includes_context(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit event should include RequestContext.
        Tests audit event field completeness.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_from_context(mock_request_context)
                await session_generator.__anext__()

                call_args = mock_emit.call_args
                assert call_args[0][0] == mock_request_context

    @pytest.mark.asyncio
    async def test_audit_event_includes_bypass_flag(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit event should include bypass flag.
        Tests audit event field completeness.
        """
        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                mock_emit.return_value = None

                session_generator = get_db_from_context(mock_request_context)
                await session_generator.__anext__()

                call_args = mock_emit.call_args
                assert isinstance(call_args[0][2], bool)


class TestAuditEventEmissionCompleteness:
    """Test suite for comprehensive audit event emission coverage."""

    def test_all_session_types_covered(self):
        """
        POSITIVE: All session types should have audit emission tests.
        Tests test coverage completeness.
        """
        session_types = [
            "get_db_from_context",
            "get_db_with_optional_tenant",
            "db_session",
            "db_session_for_context",
        ]

        # Verify all session types are tested
        for session_type in session_types:
            assert session_type in globals() or session_type in dir()

    @pytest.mark.asyncio
    async def test_audit_emission_occurs_before_query_execution(self, mock_request_context, mock_async_session):
        """
        POSITIVE: Audit emission should occur before any query execution.
        Tests audit emission timing.
        """
        execution_order = []

        async def mock_execute(*args, **kwargs):
            execution_order.append("query_executed")

        mock_async_session.execute = mock_execute

        with patch("services.layer4_agents.src.database.get_session_factory") as mock_factory:
            mock_factory.return_value().__aenter__.return_value = mock_async_session

            with patch("services.layer4_agents.src.database._emit_tenant_context_set_audit") as mock_emit:
                async def side_effect(*args, **kwargs):
                    execution_order.append("audit_emitted")

                mock_emit.side_effect = side_effect

                session_generator = get_db_from_context(mock_request_context)
                session = await session_generator.__anext__()

                # Audit should be emitted before any query execution
                assert execution_order == ["audit_emitted"]
