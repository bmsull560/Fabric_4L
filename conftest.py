"""Root conftest.py for Fabric 4L monorepo.

Ensures sys.path is set up before pytest imports any test modules.
This is necessary because pytest.ini `pythonpath` is not reliably
applied on all platforms.
"""

import sys
from pathlib import Path

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
