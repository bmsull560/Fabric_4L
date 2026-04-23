"""Test fixtures."""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
