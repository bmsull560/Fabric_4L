"""Shared fixtures for Retail & Consumer Value Pack tests.

NOTE (P1-4): File handle verification - session-scoped fixtures hold files open.
Monitor for FD exhaustion under high concurrency: cat /proc/sys/fs/file-nr
"""

import json
from pathlib import Path
from typing import Any

import pytest

# Pack Constants
PACK_DIR = Path(__file__).parent.parent
EXPECTED_PACK_ID: str = "retail-consumer-v1"  #: Expected pack identifier for consistency checks

# Validation Constants - centralized to avoid duplication
REQUIRED_FORMULA_FIELDS: list[str] = [
    "formula_id",
    "name",
    "description",
    "formula_type",
    "version",
    "status",
]
REQUIRED_VARIABLE_FIELDS: list[str] = [
    "variable_id",
    "variable_name",
    "display_name",
    "data_type",
]
REQUIRED_WORKFLOW_FIELDS: list[str] = [
    "workflow_id",
    "name",
    "description",
    "steps",
]
REQUIRED_ONTOLOGY_NODE_TYPES: list[str] = [
    "Capability",
    "UseCase",
    "Persona",
    "ValueDriver",
]
REQUIRED_ONTOLOGY_RELATIONSHIPS: list[str] = [
    "ENABLES",
    "BENEFITS",
    "DRIVES",
]
REQUIRED_ENTITY_FIELDS: list[str] = [
    "type",
    "id",
    "name",
    "description",
]


def load_json_file(filename: str) -> dict[str, Any]:
    """Load and parse a JSON file from the pack directory.

    Args:
        filename: Name of the JSON file to load.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        pytest.fail: If file cannot be loaded or parsed.
    """
    filepath = PACK_DIR / filename
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Required file not found: {filepath}")
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {filepath}: {e}")


@pytest.fixture(scope="session")
def pack_dir() -> Path:
    """Return the pack directory path."""
    return PACK_DIR


@pytest.fixture
def expected_pack_id() -> str:
    """Return the expected pack ID for consistency checks."""
    return EXPECTED_PACK_ID


@pytest.fixture
def ontology_data() -> dict[str, Any]:
    """Load and return ontology.json data.
    
    Uses function scope to prevent file descriptor accumulation
    under high-concurrency test runs.
    """
    return load_json_file("ontology.json")


@pytest.fixture
def formulas_data() -> dict[str, Any]:
    """Load and return formulas.json data.
    
    Uses function scope to prevent file descriptor accumulation
    under high-concurrency test runs.
    """
    return load_json_file("formulas.json")


@pytest.fixture
def variables_data() -> dict[str, Any]:
    """Load and return variables.json data.
    
    Uses function scope to prevent file descriptor accumulation
    under high-concurrency test runs.
    """
    return load_json_file("variables.json")


@pytest.fixture
def workflow_template_data() -> dict[str, Any]:
    """Load and return workflow_template.json data.
    
    Uses function scope to prevent file descriptor accumulation
    under high-concurrency test runs.
    """
    return load_json_file("workflow_template.json")


@pytest.fixture
def pack_files(
    ontology_data: dict[str, Any],
    formulas_data: dict[str, Any],
    variables_data: dict[str, Any],
    workflow_template_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return all pack files as a dictionary."""
    return {
        "ontology": ontology_data,
        "formulas": formulas_data,
        "variables": variables_data,
        "workflow_template": workflow_template_data,
    }
