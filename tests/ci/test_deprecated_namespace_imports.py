import importlib
import warnings
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_deprecated_namespace_imports.py"
SPEC = spec_from_file_location("check_deprecated_namespace_imports", MODULE_PATH)
check_deprecated_namespace_imports = module_from_spec(SPEC)
assert SPEC.loader is not None
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


def test_layer1_shim_emits_deprecation_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.reload(importlib.import_module("value_fabric.layer1_ingestion"))
    assert any("deprecated" in str(item.message).lower() for item in caught)


def test_layer3_shim_emits_deprecation_warning() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.reload(importlib.import_module("value_fabric.layer3_knowledge"))
    assert any("deprecated" in str(item.message).lower() for item in caught)
