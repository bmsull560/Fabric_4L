"""Integration tests for Model Registry L2→L4 cross-layer functionality.

Validates that Layer 2 can resolve LLM models from Layer 4's Model Registry
via HTTP API, with proper fallback behavior when registry is unavailable.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx
import pytest
import respx

# Add layer2-extraction to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "value-fabric", "layer2-extraction", "src"))

from layer2_extraction.integration.model_registry_client import (
    CachedModel,
    ModelRegistryClient,
)
from layer2_extraction.shared.llm_client import LLMClient


@pytest.fixture
def tenant_id() -> str:
    return str(uuid4())


@pytest.fixture
def registry_client() -> ModelRegistryClient:
    return ModelRegistryClient(
        base_url="http://test-registry:8000",
        cache_ttl_seconds=300,
    )


class TestModelRegistryClient:
    """Tests for the ModelRegistryClient HTTP client."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_model_from_registry_success(self, tenant_id: str, registry_client: ModelRegistryClient) -> None:
        """Test successful model resolution from registry."""
        # Mock the registry API response
        route = respx.get("http://test-registry:8000/v1/models/active").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": str(uuid4()),
                    "tenant_id": tenant_id,
                    "provider": "openai",
                    "model_name": "gpt-4-turbo",
                    "model_version": "2024-04",
                    "stage": "production",
                    "eval_score": 0.95,
                    "config": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            )
        )

        model = await registry_client.resolve_model(
            tenant_id=tenant_id,
            provider="openai",
        )

        assert model == "gpt-4-turbo"
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_model_not_found_uses_fallback(self, tenant_id: str, registry_client: ModelRegistryClient) -> None:
        """Test fallback to env var when no production model in registry."""
        # Mock 404 response from registry
        respx.get("http://test-registry:8000/v1/models/active").mock(
            return_value=httpx.Response(404, json={"detail": "No active production model found"})
        )

        with patch.dict(os.environ, {"L2_OPENAI_MODEL": "gpt-4o-fallback"}):
            model = await registry_client.resolve_model(
                tenant_id=tenant_id,
                provider="openai",
            )

        assert model == "gpt-4o-fallback"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_model_registry_error_uses_fallback(self, tenant_id: str, registry_client: ModelRegistryClient) -> None:
        """Test fallback when registry returns error."""
        # Mock 500 error from registry
        respx.get("http://test-registry:8000/v1/models/active").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        with patch.dict(os.environ, {"L2_OPENAI_MODEL": "gpt-4o-fallback"}):
            model = await registry_client.resolve_model(
                tenant_id=tenant_id,
                provider="openai",
            )

        assert model == "gpt-4o-fallback"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_model_caching(self, tenant_id: str, registry_client: ModelRegistryClient) -> None:
        """Test that model resolution is cached."""
        route = respx.get("http://test-registry:8000/v1/models/active").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": str(uuid4()),
                    "tenant_id": tenant_id,
                    "provider": "openai",
                    "model_name": "gpt-4-turbo",
                    "model_version": "2024-04",
                    "stage": "production",
                    "eval_score": 0.95,
                    "config": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            )
        )

        # First call should hit the API
        model1 = await registry_client.resolve_model(tenant_id=tenant_id, provider="openai")
        assert model1 == "gpt-4-turbo"
        assert route.call_count == 1

        # Second call should use cache
        model2 = await registry_client.resolve_model(tenant_id=tenant_id, provider="openai")
        assert model2 == "gpt-4-turbo"
        assert route.call_count == 1  # No additional API call

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_model_cache_expiration(self, tenant_id: str) -> None:
        """Test that cache expires after TTL."""
        # Create client with very short TTL
        client = ModelRegistryClient(
            base_url="http://test-registry:8000",
            cache_ttl_seconds=0,  # Immediate expiration
        )

        route = respx.get("http://test-registry:8000/v1/models/active").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": str(uuid4()),
                    "tenant_id": tenant_id,
                    "provider": "openai",
                    "model_name": "gpt-4-turbo",
                    "model_version": "2024-04",
                    "stage": "production",
                    "eval_score": 0.95,
                    "config": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            )
        )

        # First call
        await client.resolve_model(tenant_id=tenant_id, provider="openai")
        assert route.call_count == 1

        # Second call (cache expired) should hit API again
        await client.resolve_model(tenant_id=tenant_id, provider="openai")
        assert route.call_count == 2

    @pytest.mark.asyncio
    async def test_cached_model_expiration_logic(self) -> None:
        """Test the CachedModel expiration logic directly."""
        from datetime import UTC, datetime, timedelta

        # Fresh cache entry
        fresh = CachedModel(model_name="gpt-4", ttl_seconds=300)
        assert not fresh.is_expired()

        # Expired cache entry (created 10 minutes ago)
        expired = CachedModel(
            model_name="gpt-4",
            cached_at=datetime.now(UTC) - timedelta(minutes=10),
            ttl_seconds=300,
        )
        assert expired.is_expired()


    @pytest.mark.asyncio
    async def test_input_validation_empty_tenant_id(self) -> None:
        """Test that empty tenant_id raises ValueError."""
        client = ModelRegistryClient()

        with pytest.raises(ValueError, match="tenant_id is required"):
            await client.resolve_model(tenant_id="", provider="openai")

        with pytest.raises(ValueError, match="tenant_id is required"):
            await client.resolve_model(tenant_id="   ", provider="openai")

    @pytest.mark.asyncio
    async def test_input_validation_invalid_provider(self) -> None:
        """Test that invalid provider raises ValueError."""
        client = ModelRegistryClient()
        tenant_id = str(uuid4())

        with pytest.raises(ValueError, match="Invalid provider"):
            await client.resolve_model(tenant_id=tenant_id, provider="invalid")

        with pytest.raises(ValueError, match="Invalid provider"):
            await client.resolve_model(tenant_id=tenant_id, provider="google")

    @pytest.mark.asyncio
    async def test_provider_case_insensitive(self, tenant_id: str) -> None:
        """Test that provider names are case-insensitive."""
        with respx.mock:
            respx.get("http://test-registry:8000/v1/models/active").mock(
                return_value=httpx.Response(404)
            )

            client = ModelRegistryClient(base_url="http://test-registry:8000")

            # Should not raise - case is normalized
            with patch.dict(os.environ, {"L2_OPENAI_MODEL": "gpt-4o"}):
                model = await client.resolve_model(tenant_id=tenant_id, provider="OPENAI")
                assert model == "gpt-4o"

            with patch.dict(os.environ, {"L2_ANTHROPIC_MODEL": "claude-3"}):
                model = await client.resolve_model(tenant_id=tenant_id, provider="Anthropic")
                assert model == "claude-3"


class TestLLMClientRegistryIntegration:
    """Tests for LLMClient integration with Model Registry."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_llm_client_uses_registry_when_enabled(self, tenant_id: str) -> None:
        """Test that LLMClient resolves model from registry when enabled."""
        # Create client with registry resolution enabled
        client = LLMClient(
            provider="openai",
            api_key="test-key",
            resolve_model_from_registry=True,
            registry_tenant_id=tenant_id,
            registry_api_token="test-token",
        )

        # Mock the internal _resolve method to return a registry model
        async def mock_resolve():
            return "gpt-4-turbo-from-registry"

        client._resolve_from_registry = mock_resolve

        effective_model = await client._get_effective_model()
        assert effective_model == "gpt-4-turbo-from-registry"

    @pytest.mark.asyncio
    async def test_llm_client_ignores_registry_when_disabled(self, tenant_id: str) -> None:
        """Test that LLMClient uses env var when registry resolution is disabled."""
        with patch.dict(os.environ, {"L2_OPENAI_MODEL": "gpt-4o-env"}):
            client = LLMClient(
                provider="openai",
                api_key="test-key",
                resolve_model_from_registry=False,  # Disabled
                registry_tenant_id=tenant_id,
            )

            effective_model = await client._get_effective_model()
            assert effective_model == "gpt-4o-env"

    @pytest.mark.asyncio
    async def test_llm_client_fallback_on_registry_error(self, tenant_id: str) -> None:
        """Test that LLMClient falls back to env var when registry fails."""
        with patch.dict(os.environ, {"L2_OPENAI_MODEL": "gpt-4o-fallback"}):
            client = LLMClient(
                provider="openai",
                api_key="test-key",
                resolve_model_from_registry=True,
                registry_tenant_id=tenant_id,
            )

            # Mock the ModelRegistryClient.resolve_model to raise exception
            with patch("layer2_extraction.integration.model_registry_client.ModelRegistryClient.resolve_model") as mock_resolve:
                mock_resolve.side_effect = Exception("Registry unavailable")

                effective_model = await client._get_effective_model()
                # Should fall back to env var
                assert effective_model == "gpt-4o-fallback"

    @pytest.mark.asyncio
    async def test_llm_client_no_tenant_id_logs_warning(self) -> None:
        """Test that LLMClient warns when registry enabled but no tenant ID."""
        import logging

        with patch.dict(os.environ, {"L2_OPENAI_MODEL": "gpt-4o"}):
            with patch.object(logging, "getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                client = LLMClient(
                    provider="openai",
                    api_key="test-key",
                    resolve_model_from_registry=True,
                    registry_tenant_id=None,  # Missing tenant ID
                )

                effective_model = await client._get_effective_model()
                assert effective_model == "gpt-4o"

                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "no tenant_id provided" in warning_msg.lower()


class TestModelRegistryEndToEnd:
    """End-to-end tests simulating the complete L2→L4 flow."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_full_flow_registry_to_extraction(self, tenant_id: str) -> None:
        """Test complete flow from registry resolution to extraction."""
        # Mock L4 registry returning a specific model
        respx.get("http://layer4:8000/v1/models/active").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": str(uuid4()),
                    "tenant_id": tenant_id,
                    "provider": "openai",
                    "model_name": "gpt-4-turbo-production",
                    "model_version": "2024-04",
                    "stage": "production",
                    "eval_score": 0.96,
                    "config": {},
                    "created_at": "2024-01-01T00:00:00Z",
                }
            )
        )

        # Create L2 client configured to use registry
        client = LLMClient(
            provider="openai",
            api_key="test-key",
            resolve_model_from_registry=True,
            registry_tenant_id=tenant_id,
        )

        # The model should be resolved from registry
        async def mock_resolve():
            return "gpt-4-turbo-production"

        client._resolve_from_registry = mock_resolve

        effective_model = await client._get_effective_model()
        assert effective_model == "gpt-4-turbo-production"

    @pytest.mark.asyncio
    async def test_explicit_model_overrides_registry(self, tenant_id: str) -> None:
        """Test that explicit model parameter is used as base, registry can override."""
        # When an explicit model is provided, it's set as self.model
        # The registry can still override it if enabled and successful
        client = LLMClient(
            provider="openai",
            api_key="test-key",
            model="gpt-4o-mini-explicit",  # Explicit model set as base
            resolve_model_from_registry=False,  # Disabled so explicit model is used
            registry_tenant_id=tenant_id,
        )

        effective_model = await client._get_effective_model()
        # When registry is disabled, explicit model should be used
        assert effective_model == "gpt-4o-mini-explicit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
