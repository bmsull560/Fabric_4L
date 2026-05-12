from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_layer5_shim_integrity.py"
SPEC = spec_from_file_location("check_layer5_shim_integrity", MODULE_PATH)
check_layer5_shim_integrity = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_layer5_shim_integrity)


def test_layer5_compatibility_tree_is_shim_only() -> None:
    assert check_layer5_shim_integrity.main() == 0
