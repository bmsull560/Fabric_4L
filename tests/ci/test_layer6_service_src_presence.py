from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER6_SRC = REPO_ROOT / "services" / "layer6-benchmarks" / "src"
REQUIRED_WRAPPERS = [
    LAYER6_SRC / "__init__.py",
    LAYER6_SRC / "api" / "__init__.py",
    LAYER6_SRC / "api" / "main.py",
    LAYER6_SRC / "api" / "deps.py",
    LAYER6_SRC / "api" / "schemas.py",
    LAYER6_SRC / "api" / "routes" / "__init__.py",
    LAYER6_SRC / "api" / "routes" / "benchmarks.py",
    LAYER6_SRC / "api" / "routes" / "system.py",
    LAYER6_SRC / "database.py",
    LAYER6_SRC / "shared_bootstrap.py",
]


def test_layer6_service_src_directory_exists() -> None:
    assert LAYER6_SRC.is_dir(), f"Missing required Layer 6 service source directory: {LAYER6_SRC}"


def test_layer6_service_entrypoint_exists() -> None:
    entrypoint = LAYER6_SRC / "api" / "main.py"
    assert entrypoint.is_file(), f"Missing Layer 6 API entrypoint required by Docker CMD: {entrypoint}"


def test_layer6_service_required_wrapper_files_exist() -> None:
    missing = [path for path in REQUIRED_WRAPPERS if not path.is_file()]
    assert not missing, "Missing required Layer 6 service wrapper files:\n" + "\n".join(str(path) for path in missing)


def test_layer6_service_tests_do_not_need_sys_path_hacks() -> None:
    pytest_ini = (REPO_ROOT / "pytest.ini").read_text(encoding="utf-8")
    conftest = (REPO_ROOT / "services" / "layer6-benchmarks" / "tests" / "conftest.py").read_text(encoding="utf-8")

    assert "services/layer6-benchmarks" in pytest_ini
    assert "sys.path.insert" not in conftest
