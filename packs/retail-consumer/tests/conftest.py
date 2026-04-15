"""Shared fixtures for Retail & Consumer Value Pack tests."""

import json
from pathlib import Path
from typing import Any

import pytest

# Constants
PACK_DIR = Path(__file__).parent.parent
EXPECTED_PACK_ID = "retail-consumer-v1"
REQUIRED_FORMULA_FIELDS = [
    "formula_id",
    "name",
    "description",
    "formula_type",
    "version",
    "status",
]
REQUIRED_VARIABLE_FIELDS = [
    "variable_id",
    "variable_name",
    "display_name",
    "data_type",
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


@pytest.fixture(scope="session")
def expected_pack_id() -> str:
    """Return the expected pack ID for consistency checks."""
    return EXPECTED_PACK_ID


@pytest.fixture(scope="session")
def ontology_data() -> dict[str, Any]:
    """Load and return ontology.json data."""
    return load_json_file("ontology.json")


@pytest.fixture(scope="session")
def formulas_data() -> dict[str, Any]:
    """Load and return formulas.json data."""
    return load_json_file("formulas.json")


@pytest.fixture(scope="session")
def variables_data() -> dict[str, Any]:
    """Load and return variables.json data."""
    return load_json_file("variables.json")


@pytest.fixture(scope="session")
def workflow_template_data() -> dict[str, Any]:
    """Load and return workflow_template.json data."""
    return load_json_file("workflow_template.json")


@pytest.fixture(scope="session")
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
