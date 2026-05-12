"""Regression guard for Layer 3 models canonical/shim topology."""

from pathlib import Path

CANONICAL_MODELS = Path("value_fabric/layer3/api/models.py")
COMPAT_MODELS = Path("services/layer3-knowledge/src/api/models.py")


EXPECTED_COMPAT_CONTENT = '"""Compatibility shim for Layer 3 API models.\n\nCanonical implementation lives in ``value_fabric.layer3.api.models`` per\n``docs/reference/layer-runtime-path-governance.md``.\n"""\n\nfrom value_fabric.layer3.api.models import *  # noqa: F401,F403\n'


def test_layer3_canonical_models_is_substantive() -> None:
    canonical_source = CANONICAL_MODELS.read_text(encoding="utf-8")

    assert "class HealthResponse(BaseModel):" in canonical_source
    assert "class GraphRAGResponse(BaseModel):" in canonical_source
    assert "from pydantic import (" in canonical_source


def test_layer3_compat_models_remains_shim_only() -> None:
    compat_source = COMPAT_MODELS.read_text(encoding="utf-8")

    assert compat_source == EXPECTED_COMPAT_CONTENT
    assert "class " not in compat_source
    assert "from pydantic import" not in compat_source
