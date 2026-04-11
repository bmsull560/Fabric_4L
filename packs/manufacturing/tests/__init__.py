"""Manufacturing Value Pack Test Suite.

Integration tests for validating pack integrity, formula execution,
and ontology relationship consistency.
"""

import json
from pathlib import Path
from typing import Any

PACK_DIR = Path(__file__).parent.parent


def load_pack_file(filename: str) -> dict[str, Any]:
    """Load a JSON file from the pack directory."""
    with open(PACK_DIR / filename) as f:
        return json.load(f)
