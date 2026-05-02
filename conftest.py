"""Root conftest.py for Fabric 4L monorepo.

Ensures sys.path is set up before pytest imports any test modules.
Only adds the shared package path. Layer test directories are expected
to add their own src paths in their local conftest.py files.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.resolve()

# Shared package (canonical location)
_SHARED_SRC = _REPO_ROOT / "packages" / "shared" / "src"
if _SHARED_SRC.exists() and str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))
