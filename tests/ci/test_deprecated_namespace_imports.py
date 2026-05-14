import importlib
import importlib.util
import sys
import warnings
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_deprecated_namespace_imports.py"
SPEC = spec_from_file_location("check_deprecated_namespace_imports", MODULE_PATH)
check_deprecated_namespace_imports = module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["check_deprecated_namespace_imports"] = check_deprecated_namespace_imports
SPEC.loader.exec_module(check_deprecated_namespace_imports)


def test_namespace_scanner_passes_clean_repo() -> None:
    assert check_deprecated_namespace_imports.main([]) == 0


def test_namespace_scanner_detects_deprecated_import(tmp_path) -> None:
    (tmp_path / "services/demo").mkdir(parents=True)
    sample = tmp_path / "services/demo/sample.py"
    sample.write_text("from value_fabric.layer1_ingestion.src import api\n", encoding="utf-8")
    assert check_deprecated_namespace_imports.main(["--repo-root", str(tmp_path), "--strict"]) == 1


def test_namespace_scanner_allows_baseline_findings(tmp_path) -> None:
    (tmp_path / "services/demo").mkdir(parents=True)
    sample = tmp_path / "services/demo/sample.py"
    statement = "from value_fabric.layer1_ingestion.src import api"
    sample.write_text(statement + "\n", encoding="utf-8")
    baseline_dir = tmp_path / "docs/reference"
    baseline_dir.mkdir(parents=True)
    (baseline_dir / "deprecated-namespace-import-baseline.json").write_text(
        "["
        '{"path":"services/demo/sample.py","line":1,'
        '"statement":"from value_fabric.layer1_ingestion.src import api",'
        '"deprecated_namespace":"value_fabric.layer1_ingestion"}'
        "]",
        encoding="utf-8",
    )
    assert (
        check_deprecated_namespace_imports.main(
            ["--repo-root", str(tmp_path), "--strict", "--use-baseline"]
        )
        == 0
    )


def test_deleted_namespaces_no_longer_importable() -> None:
    """Legacy namespace packages were removed; importing them must fail."""
    import importlib

    for dead in ("value_fabric.layer1_ingestion", "value_fabric.layer3_knowledge"):
        spec = importlib.util.find_spec(dead)
        assert spec is None, f"Expected {dead} to be unimportable after cleanup"
