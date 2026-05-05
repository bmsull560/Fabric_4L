from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, cast

_SHARED_SRC = Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"
if str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))

_framework_app = import_module("value_fabric.shared.fastapi_framework.app")
_framework_middleware = import_module("value_fabric.shared.fastapi_framework.middleware")
_observability = import_module("value_fabric.shared.observability.metrics_access")
_security_config = import_module("value_fabric.shared.security.config")
_security_middleware = import_module("value_fabric.shared.security.middleware")

build_health_response = cast(Callable[..., dict[str, Any]], _framework_app.build_health_response)
create_fabric_app = cast(Callable[..., Any], _framework_app.create_fabric_app)
register_health_endpoint = cast(Callable[..., None], _framework_app.register_health_endpoint)
resolve_cors_policy = cast(Callable[..., Any], _framework_middleware.resolve_cors_policy)
verify_metrics_access = cast(Callable[..., bool], _observability.verify_metrics_access)
validate_production_safety = cast(Callable[..., None], _security_config.validate_production_safety)
SecurityConfig = _security_middleware.SecurityConfig
add_security_middleware = cast(Callable[..., None], _security_middleware.add_security_middleware)