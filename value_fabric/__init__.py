"""Compatibility package for value_fabric namespace.

This module forwards imports to the canonical value-fabric/ implementation.
Tests and consumers should use: from value_fabric.layerX import ...
"""

import importlib.util
import sys
from pathlib import Path

# Get the actual implementation directory
_REPO_ROOT = Path(__file__).parent.parent.resolve()
_CANONICAL_DIR = _REPO_ROOT / "value-fabric"

# Add canonical src directories to path for layer imports
_LAYER_PATHS = [
    _CANONICAL_DIR / "layer1-ingestion" / "src",
    _CANONICAL_DIR / "layer2-extraction" / "src",
    _CANONICAL_DIR / "layer3-knowledge" / "src",
    _CANONICAL_DIR / "layer4-agents" / "src",
    _CANONICAL_DIR / "layer5-ground-truth" / "src",
    _CANONICAL_DIR / "layer6-benchmarks" / "src",
]

for _path in _LAYER_PATHS:
    if _path.exists() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

# Forward shared imports to canonical location
_shared_path = _CANONICAL_DIR / "shared"
if _shared_path.exists() and str(_shared_path) not in sys.path:
    sys.path.insert(0, str(_shared_path))
