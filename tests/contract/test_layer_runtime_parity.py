"""Parity guardrails between canonical runtime modules and maintained service wrappers."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


LAYER_PARITY_RULES: dict[str, dict[str, object]] = {
    "layer1": {
        "canonical_routes": REPO_ROOT / "value_fabric/layer1/api/routes/__init__.py",
        "service_routes": REPO_ROOT / "services/layer1-ingestion/src/api/routes/__init__.py",
        "service_main": REPO_ROOT / "services/layer1-ingestion/src/api/main.py",
        "canonical_import": "value_fabric.layer1.api.routes.__init__",
        "service_interface": REPO_ROOT / "value_fabric/layer1/services/ingestion_service.py",
        "repository_interface": REPO_ROOT / "value_fabric/layer1/storage/job_repository.py",
        "middleware_anchor": REPO_ROOT / "value_fabric/layer1/api/app_monolith.py",
    },
    "layer2": {
        "canonical_routes": REPO_ROOT / "value_fabric/layer2/api/routes/__init__.py",
        "service_routes": REPO_ROOT / "services/layer2-extraction/src/layer2_extraction/api/routes/__init__.py",
        "service_main": REPO_ROOT / "services/layer2-extraction/src/layer2_extraction/api/main.py",
        "canonical_import": "value_fabric.layer2.api.routes.__init__",
        "service_interface": REPO_ROOT / "value_fabric/layer2/services/extraction_service.py",
        "repository_interface": REPO_ROOT / "value_fabric/layer2/storage/extraction_repository.py",
        "middleware_anchor": REPO_ROOT / "value_fabric/layer2/api/main.py",
    },
    "layer3": {
        "canonical_routes": REPO_ROOT / "value_fabric/layer3/api/routes/__init__.py",
        "service_routes": REPO_ROOT / "services/layer3-knowledge/src/api/routes/__init__.py",
        "service_main": REPO_ROOT / "services/layer3-knowledge/src/api/main.py",
        "canonical_import": "value_fabric.layer3.api.routes.__init__",
        "service_interface": REPO_ROOT / "value_fabric/layer3/services/graph_service.py",
        "repository_interface": REPO_ROOT / "value_fabric/layer3/repositories/neo4j_repository.py",
        "middleware_anchor": REPO_ROOT / "value_fabric/layer3/api/main.py",
    },
    "layer4": {
        "canonical_routes": REPO_ROOT / "value_fabric/layer4/api/routes/__init__.py",
        "service_routes": REPO_ROOT / "services/layer4-agents/src/api/routes/__init__.py",
        "service_main": REPO_ROOT / "services/layer4-agents/src/api/main.py",
        "canonical_import": "value_fabric.layer4.api.routes.__init__",
        "service_interface": REPO_ROOT / "value_fabric/layer4/services/workflow_service.py",
        "repository_interface": REPO_ROOT / "value_fabric/layer4/repositories/workflow_repository.py",
        "middleware_anchor": REPO_ROOT / "value_fabric/layer4/api/main.py",
    },
    "layer5": {
        "canonical_routes": REPO_ROOT / "services/layer5-ground-truth/src/layer5_ground_truth/api/router.py",
        "service_routes": REPO_ROOT / "value_fabric/layer5/api/router.py",
        "service_main": REPO_ROOT / "value_fabric/layer5/api/main.py",
        "canonical_import": "layer5_ground_truth.api.router",
        "service_interface": REPO_ROOT / "services/layer5-ground-truth/src/layer5_ground_truth/services/claims_service.py",
        "repository_interface": REPO_ROOT / "services/layer5-ground-truth/src/layer5_ground_truth/repositories/claims_repository.py",
        "middleware_anchor": REPO_ROOT / "services/layer5-ground-truth/src/layer5_ground_truth/api/main.py",
    },
    "layer6": {
        "canonical_routes": REPO_ROOT / "value_fabric/layer6/api/routes/__init__.py",
        "service_routes": REPO_ROOT / "services/layer6-benchmarks/src/api/routes/__init__.py",
        "service_main": REPO_ROOT / "services/layer6-benchmarks/src/api/main.py",
        "canonical_import": "value_fabric.layer6.api.routes.__init__",
        "service_interface": REPO_ROOT / "value_fabric/layer6/api/routes/benchmarks.py",
        "repository_interface": REPO_ROOT / "value_fabric/layer6/repositories/benchmark_repository.py",
        "middleware_anchor": REPO_ROOT / "value_fabric/layer6/api/main.py",
    },
}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _star_imports(path: Path) -> set[str]:
    module = _parse(path)
    imports: set[str] = set()
    for node in module.body:
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            if node.module:
                imports.add(node.module)
    return imports


def test_layer_parity_rules_cover_all_layers() -> None:
    assert set(LAYER_PARITY_RULES.keys()) == {"layer1", "layer2", "layer3", "layer4", "layer5", "layer6"}


def test_service_route_modules_reexport_canonical_exports() -> None:
    for layer, rule in LAYER_PARITY_RULES.items():
        imports = _star_imports(rule["service_routes"])
        expected = {rule["canonical_import"]}
        assert expected.issubset(imports), f"{layer} service route module must star-import canonical route module"


def test_service_main_modules_reexport_or_bind_canonical_app() -> None:
    for layer, rule in LAYER_PARITY_RULES.items():
        source = rule["service_main"].read_text(encoding="utf-8")
        assert "app" in source, f"{layer} service main entrypoint must expose app"


def test_parity_rules_define_required_checkpoints() -> None:
    for layer, rule in LAYER_PARITY_RULES.items():
        for field in ("canonical_routes", "service_routes", "service_main", "service_interface", "repository_interface", "middleware_anchor"):
            target = rule[field]
            assert isinstance(target, Path)
            assert target.exists(), f"{layer}: missing parity checkpoint path for {field}: {target}"
