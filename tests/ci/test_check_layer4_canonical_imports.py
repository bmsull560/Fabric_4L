from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_layer4_canonical_imports.py"
SPEC = spec_from_file_location("check_layer4_canonical_imports", MODULE_PATH)
module = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def test_layer4_imports_are_canonical() -> None:
    assert module.main() == 0
