"""I-03 production safety tests for Layer 2 LLM client.

Verifies that the LLM client requires valid API keys and does not have
a mock mode in production-like environments.
"""

from __future__ import annotations

import os

import pytest


def _clear_layer2_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("ENVIRONMENT", "APP_ENV", "LAYER2_ENV", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)


class TestLayer2LLMClientProductionSafety:
    def test_openai_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
        """OpenAI client must raise ValueError when API key is not configured."""
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")

        from layer2_extraction.shared.llm_client import LLMClient

        with pytest.raises(ValueError, match="OpenAI API key required"):
            LLMClient(provider="openai")

    def test_anthropic_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
        """Anthropic client must raise ValueError when API key is not configured."""
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")

        from layer2_extraction.shared.llm_client import LLMClient

        with pytest.raises(ValueError, match="Anthropic API key required"):
            LLMClient(provider="anthropic")

    def test_openai_client_accepts_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
        """OpenAI client should accept API key from environment variable."""
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        from layer2_extraction.shared.llm_client import LLMClient

        client = LLMClient(provider="openai")
        assert client.provider.value == "openai"

    def test_anthropic_client_accepts_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
        """Anthropic client should accept API key from environment variable."""
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        from layer2_extraction.shared.llm_client import LLMClient

        client = LLMClient(provider="anthropic")
        assert client.provider.value == "anthropic"

    def test_llm_client_has_no_mock_provider_mode(monkeypatch: pytest.MonkeyPatch) -> None:
        """LLMClient should not have a 'mock' provider option - only real providers."""
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")

        from layer2_extraction.shared.llm_client import LLMClient, LLMProvider

        # Verify only real providers are supported
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"

        # Attempting to use 'mock' should fail
        with pytest.raises(ValueError, match="'mock' is not a valid LLMProvider"):
            LLMClient(provider="mock")

    def test_openai_client_fails_without_package(monkeypatch: pytest.MonkeyPatch) -> None:
        """OpenAI client should fail gracefully if openai package is not installed."""
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        # Temporarily remove openai from sys.modules to simulate missing package
        import sys

        openai_module = sys.modules.pop("openai", None)

        try:
            # Re-import to trigger the ImportError check
            import importlib

            import layer2_extraction.shared.llm_client
            importlib.reload(layer2_extraction.shared.llm_client)

            from layer2_extraction.shared.llm_client import LLMClient

            with pytest.raises(ImportError, match="openai package not installed"):
                LLMClient(provider="openai")
        finally:
            # Restore openai module if it was present
            if openai_module is not None:
                sys.modules["openai"] = openai_module
