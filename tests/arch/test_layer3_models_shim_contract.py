"""Architecture contract for Layer 3 models compatibility shim."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SHIM_PATH = REPO_ROOT / "services/layer3-knowledge/src/api/models.py"


def test_layer3_models_shim_is_reexport_only() -> None:
    content = SHIM_PATH.read_text(encoding="utf-8")
    assert "from value_fabric.layer3.api.models import *" in content
    assert "class " not in content
    assert "def " not in content
