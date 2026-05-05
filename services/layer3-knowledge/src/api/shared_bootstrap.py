from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Callable, cast

_SHARED_SRC = Path(__file__).resolve().parents[4] / "packages" / "shared" / "src"
if str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))

_observability = import_module("value_fabric.shared.observability.metrics_access")

verify_metrics_access = cast(Callable[..., bool], _observability.verify_metrics_access)