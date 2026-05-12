"""Auth dependency contract tests for state inspector routes."""

from __future__ import annotations

import inspect

from fastapi.params import Depends

from services.layer4_agents.src.api.routes import state_inspector
from value_fabric.shared.identity.dependencies import require_authenticated


def test_analyze_errors_requires_authenticated_dependency() -> None:
    """Error inspection route must require authenticated context."""

    signature = inspect.signature(state_inspector.analyze_errors)
    ctx_param = signature.parameters.get("_ctx")

    assert ctx_param is not None
    assert isinstance(ctx_param.default, Depends)
    assert ctx_param.default.dependency is require_authenticated
