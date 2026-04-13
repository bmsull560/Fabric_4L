"""Shared fixtures for agent evaluation tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).parent.parent.parent


def load_fixture(name: str) -> dict[str, Any]:
    """Load a golden-trace fixture file by skill name."""
    path = FIXTURES_DIR / f"{name}_traces.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def semantic_search_traces() -> dict[str, Any]:
    return load_fixture("semantic_search")


@pytest.fixture
def evaluate_formula_traces() -> dict[str, Any]:
    return load_fixture("evaluate_formula")


@pytest.fixture
def mock_knowledge_graph() -> MagicMock:
    """Mock Neo4j driver that returns canned entity results."""
    mock = MagicMock()
    mock.run = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock LLM client — prevents real API calls in unit evals."""
    mock = MagicMock()
    mock.chat = AsyncMock(return_value=MagicMock(content="mocked response"))
    return mock
