"""Guardrails ensuring ValuePack models have a single canonical source."""

from pathlib import Path


def test_service_valuepack_module_is_forwarder_only() -> None:
    module_path = Path("services/layer3-knowledge/src/models/valuepack.py")
    content = module_path.read_text(encoding="utf-8")

    assert "from value_fabric.layer3.models.valuepack import *" in content
    forbidden_tokens = ("class ", "def ", "field_validator", "BaseModel", "Enum")
    assert not any(token in content for token in forbidden_tokens), (
        "services/layer3-knowledge/src/models/valuepack.py must remain a pure "
        "import-forwarder to value_fabric.layer3.models.valuepack"
    )
