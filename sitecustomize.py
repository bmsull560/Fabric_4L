"""Site customization for Fabric 4L monorepo.

Sets up sys.path so that namespace packages under value_fabric/ resolve
correctly across packages/shared/src/ and services/*/src/.
"""

import sys
from pathlib import Path

# Debug: confirm this module loaded at startup
_LOADED = True

_REPO_ROOT = Path(__file__).parent.resolve()

# Shared package
_SHARED_SRC = _REPO_ROOT / "packages" / "shared" / "src"
if _SHARED_SRC.exists() and str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))

# Service layers
_LAYERS = [
    "layer1-ingestion",
    "layer2-extraction",
    "layer3-knowledge",
    "layer4-agents",
    "layer5-ground-truth",
    "layer6-benchmarks",
]

for _layer in _LAYERS:
    _src = _REPO_ROOT / "services" / _layer / "src"
    if _src.exists() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
