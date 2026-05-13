from __future__ import annotations

import importlib
import importlib.util
import inspect
import sys
import warnings
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER5_SRC = REPO_ROOT / "services" / "layer5-ground-truth" / "src"
if str(LAYER5_SRC) not in sys.path:
    sys.path.insert(0, str(LAYER5_SRC))


def _load_by_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _import_module(name: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return importlib.import_module(name)


def _public_api(module) -> set[str]:
    explicit = getattr(module, "__all__", None)
    if explicit:
        return set(explicit)
    return {name for name in dir(module) if not name.startswith("_")}


def _assert_symbol_parity(canonical, shimmed, expected_names: list[str]) -> None:
    canonical_api = _public_api(canonical)
    shimmed_api = _public_api(shimmed)

    assert set(expected_names).issubset(canonical_api)
    assert set(expected_names).issubset(shimmed_api)
    assert canonical_api == shimmed_api

    for name in expected_names:
        canonical_value = getattr(canonical, name)
        shimmed_value = getattr(shimmed, name)
        assert type(canonical_value) is type(shimmed_value)
        if callable(canonical_value) and callable(shimmed_value):
            assert str(inspect.signature(canonical_value)) == str(inspect.signature(shimmed_value))
        if hasattr(canonical_value, "routes") and hasattr(shimmed_value, "routes"):
            assert [route.path for route in canonical_value.routes] == [route.path for route in shimmed_value.routes]


@pytest.mark.parametrize(
    ("surface", "canonical_name", "shim_name", "shim_path", "expected_names", "env_overrides"),
    [
        (
            "layer1 compatibility routes",
            "value_fabric.layer1.api.routes.compatibility",
            None,
            REPO_ROOT / "services" / "layer1-ingestion" / "src" / "api" / "routes" / "compatibility.py",
            [
                "router",
                "short_ingest_compatibility_boundary",
                "create_ingestion_source_compatibility_boundary",
            ],
            {},
        ),
        (
            "layer3 compat aliases",
            "value_fabric.layer3.api.routes.compat_aliases",
            None,
            REPO_ROOT / "services" / "layer3-knowledge" / "src" / "api" / "routes" / "compat_aliases.py",
            ["router", "graph_rag_legacy_alias", "hybrid_search_aliases"],
            {},
        ),
        (
            "layer3 entity compat",
            "value_fabric.layer3.api.routes.entity_compat",
            None,
            REPO_ROOT / "services" / "layer3-knowledge" / "src" / "api" / "routes" / "entity_compat.py",
            ["router"],
            {},
        ),
        (
            "layer4 main entrypoint",
            "value_fabric.layer4.main",
            "layer4_agents.main",
            None,
            ["app"],
            {
                "LAYER1_API_URL": "http://127.0.0.1:8001",
                "LAYER2_API_URL": "http://127.0.0.1:8002",
                "LAYER3_API_URL": "http://127.0.0.1:8003",
                "LAYER4_LAYER5_API_URL": "http://127.0.0.1:8005",
            },
        ),
        (
            "layer5 truth object",
            "layer5_ground_truth.models.truth_object",
            "value_fabric.layer5.models.truth_object",
            None,
            ["TruthObject", "TruthStatus", "ValidationEvent"],
            {},
        ),
    ],
)
def test_shim_surfaces_match_canonical_public_api(
    surface: str,
    canonical_name: str,
    shim_name: str | None,
    shim_path: Path | None,
    expected_names: list[str],
    env_overrides: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)
    if surface == "layer4 main entrypoint":
        for name in ("value_fabric.layer4.main", "layer4_agents.main"):
            sys.modules.pop(name, None)

    canonical = _import_module(canonical_name)
    shimmed = _import_module(shim_name) if shim_name else _load_by_path(shim_path, f"shim_test_{shim_path.stem}")

    _assert_symbol_parity(canonical, shimmed, expected_names)
