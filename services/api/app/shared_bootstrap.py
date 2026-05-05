from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, cast

_SHARED_SRC = Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"
if str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))

_framework_app = import_module("value_fabric.shared.fastapi_framework.app")
_security_config = import_module("value_fabric.shared.security.config")

create_fabric_app = cast(Callable[..., Any], _framework_app.create_fabric_app)
register_health_endpoint = cast(Callable[..., None], _framework_app.register_health_endpoint)
validate_production_safety = cast(Callable[..., None], _security_config.validate_production_safety)