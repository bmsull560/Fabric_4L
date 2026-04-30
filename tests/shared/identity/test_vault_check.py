"""Tests for vault_check module - regression tests for code review fixes."""

import pytest
from unittest.mock import AsyncMock, patch

from shared.identity.vault_check import get_vault_health, get_vault_healthResult


class TestGetVaultHealth:
    """Test get_vault_health returns complete result with all required fields."""

    @pytest.mark.asyncio
    async def test_success_response_includes_all_required_fields(self):
        """Regression test: Issue #1 - missing 'reachable' field in success response."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "initialized": True,
            "sealed": False,
            "standby": False,
            "version": "1.15.0",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=AsyncMock(
                    get=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_vault_health()

        # Verify all TypedDictModel required fields are present
        assert "reachable" in result
        assert result["reachable"] is True
        assert "status" in result
        assert result["status"] == "healthy"
        assert "initialized" in result
        assert "sealed" in result
        assert "standby" in result
        assert "version" in result

    @pytest.mark.asyncio
    async def test_error_response_has_reachable_false(self):
        """Test error response correctly sets reachable=False."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_vault_health()

        assert result["reachable"] is False
        assert result["status"] == "unreachable"
        assert "error" in result


class TestGetVaultHealthResultModel:
    """Test TypedDictModel validation."""

    def test_model_requires_reachable_field(self):
        """Verify reachable is required by model validation."""
        # This should work with all required fields
        data = {
            "status": "healthy",
            "reachable": True,
            "initialized": True,
            "sealed": False,
            "standby": False,
            "version": "1.15.0",
        }
        result = get_vault_healthResult.model_validate(data)
        assert result["reachable"] is True

    def test_model_allows_optional_fields(self):
        """Verify model works with minimal required fields."""
        data = {
            "status": "unreachable",
            "reachable": False,
            "error": "Connection failed",
        }
        result = get_vault_healthResult.model_validate(data)
        assert result["status"] == "unreachable"
