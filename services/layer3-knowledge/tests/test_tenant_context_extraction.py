"""Tests for tenant context extraction helper (Sprint 5).

Validates that _extract_tenant_id() correctly extracts tenant context
from FastAPI request objects for multi-tenant security.
"""

import uuid
from unittest.mock import MagicMock

import pytest

# Import the helper under test
from value_fabric.layer3.api.app_monolith import _extract_tenant_id


class TestExtractTenantId:
    """Test suite for _extract_tenant_id() helper function."""

    def test_extracts_tenant_id_from_request_context(self):
        """Should extract tenant_id from request.state.governance_context when available."""
        # Arrange
        mock_context = MagicMock()
        mock_context.tenant_id = uuid.uuid4()
        
        mock_request = MagicMock()
        mock_request.state.governance_context = mock_context
        
        # Act
        result = _extract_tenant_id(mock_request)
        
        # Assert
        assert result is not None
        assert result == str(mock_context.tenant_id)

    def test_returns_none_when_no_tenant_context(self):
        """Should return None when request has no tenant context."""
        # Arrange
        mock_request = MagicMock()
        mock_request.state.governance_context = MagicMock()
        mock_request.state.governance_context.tenant_id = None
        
        # Act
        result = _extract_tenant_id(mock_request)
        
        # Assert
        assert result is None

    def test_returns_none_when_no_context_attribute(self):
        """Should return None when request.state has no governance_context."""
        # Arrange
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.governance_context = None
        
        # Act
        result = _extract_tenant_id(mock_request)
        
        # Assert
        assert result is None

    def test_returns_none_when_request_is_none(self):
        """Should return None when request parameter is None."""
        # Act
        result = _extract_tenant_id(None)
        
        # Assert
        assert result is None

    def test_converts_tenant_id_to_string(self):
        """Should convert UUID tenant_id to string."""
        # Arrange
        tenant_uuid = uuid.uuid4()
        mock_context = MagicMock()
        mock_context.tenant_id = tenant_uuid
        
        mock_request = MagicMock()
        mock_request.state.governance_context = mock_context
        
        # Act
        result = _extract_tenant_id(mock_request)
        
        # Assert
        assert isinstance(result, str)
        assert result == str(tenant_uuid)

    def test_handles_string_tenant_id(self):
        """Should handle string tenant_id without conversion issues."""
        # Arrange
        mock_context = MagicMock()
        mock_context.tenant_id = "tenant-123-abc"
        
        mock_request = MagicMock()
        mock_request.state.governance_context = mock_context
        
        # Act
        result = _extract_tenant_id(mock_request)
        
        # Assert
        assert result == "tenant-123-abc"

    def test_integration_with_real_request_context(self):
        """Integration test with actual RequestContext from shared.identity."""
        try:
            from value_fabric.shared.identity.context import RequestContext
            
            # Arrange
            tenant_id = uuid.uuid4()
            ctx = RequestContext(
                tenant_id=tenant_id,
                user_id=uuid.uuid4(),
                request_id="test-req-123"
            )
            
            mock_request = MagicMock()
            mock_request.state.governance_context = ctx
            
            # Act
            result = _extract_tenant_id(mock_request)
            
            # Assert
            assert result == str(tenant_id)
        except ImportError:
            pytest.skip("shared.identity.context not available")


class TestExtractTenantIdDeterminism:
    """Verify deterministic behavior across multiple calls."""

    def test_returns_consistent_result_on_repeated_calls(self):
        """Should return same result for same input (deterministic)."""
        # Arrange
        tenant_uuid = uuid.uuid4()
        mock_context = MagicMock()
        mock_context.tenant_id = tenant_uuid
        
        mock_request = MagicMock()
        mock_request.state.governance_context = mock_context
        
        # Act - call multiple times
        results = [_extract_tenant_id(mock_request) for _ in range(5)]
        
        # Assert - all results identical
        assert all(r == results[0] for r in results)
        assert results[0] == str(tenant_uuid)



def test_extract_ignores_module_availability_flag(monkeypatch):
    """Extraction remains context-only when optional tenant module is unavailable."""
    monkeypatch.setattr("value_fabric.layer3.api.app_monolith.NEO4J_TENANT_AVAILABLE", False)
    mock_context = MagicMock()
    mock_context.tenant_id = "tenant-module-off"

    mock_request = MagicMock()
    mock_request.state.governance_context = mock_context

    assert _extract_tenant_id(mock_request) == "tenant-module-off"
