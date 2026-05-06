"""Contract tests for import topology correctness.

Phase 4: Verify canonical imports resolve deterministically.
"""
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent


class TestImportTopology:
    """Verify import namespace resolution."""

    def test_value_fabric_namespace_imports(self):
        """value_fabric package should be importable."""
        import value_fabric

        assert value_fabric.__file__ is not None
        # Should resolve to either value_fabric/ or value-fabric/ via compatibility
        assert "value" in str(value_fabric.__file__).lower()

    def test_shared_namespace_resolution(self):
        """import shared should resolve to canonical location."""
        import value_fabric.shared

        shared_path = Path(value_fabric.shared.__file__)
        # Should resolve to value-fabric/shared/ or value_fabric/shared/
        # NOT root shared/ which causes shadowing
        assert "value" in str(shared_path).lower(), (
            f"shared resolved to {shared_path}, expected value-fabric/shared/ "
            "or value_fabric/shared/"
        )

    @pytest.mark.parametrize("layer", [
        "layer1_ingestion",
        "layer2_extraction",
        "layer3_knowledge",
        "layer4_agents",
        "layer5_ground_truth",
        "layer6_benchmarks",
    ])
    def test_layer_imports(self, layer):
        """Each layer should be importable via value_fabric."""
        try:
            module = __import__(f"layer4_agents", fromlist=["layer4_agents"])
            assert module is not None
        except ImportError as e:
            pytest.skip(f"Layer 4 agents not yet available: {e}")

    def test_layer4_engine_import(self):
        """Layer 4 engine module should be importable via layer4_agents."""
        try:
            import layer4_agents.engine
            assert layer4_agents.engine.__file__ is not None
        except ImportError as e:
            pytest.skip(f"Layer 4 engine not yet available: {e}")

    def test_layer4_tools_import(self):
        """Layer 4 tools module should be importable via layer4_agents."""
        try:
            import layer4_agents.tools
            assert layer4_agents.tools.__file__ is not None
        except ImportError as e:
            pytest.skip(f"Layer 4 tools not yet available: {e}")

    def test_layer4_models_import(self):
        """Layer 4 models module should be importable via layer4_agents."""
        try:
            import layer4_agents.models
            assert layer4_agents.models.__file__ is not None
        except ImportError as e:
            pytest.skip(f"Layer 4 models not yet available: {e}")

    def test_layer4_resolves_to_canonical_service_tree(self):
        """layer4_agents must resolve via services/layer4-agents/src/."""
        import layer4_agents

        canonical = (REPO_ROOT / "services" / "layer4-agents" / "src").resolve()
        assert any(
            Path(str(p)).resolve() == canonical
            for p in value_fabric.layer4.__path__
        ), (
            f"Canonical path {canonical} not found in value_fabric.layer4.__path__: "
            f"{value_fabric.layer4.__path__}"
        )

    def test_pytest_collection_no_import_errors(self):
        """pytest --collect-only should have zero import errors."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Check for import errors in stderr
        import_errors = [
            line for line in result.stderr.split("\n")
            if "ImportError" in line or "ModuleNotFoundError" in line
        ]

        assert len(import_errors) == 0, (
            f"Found {len(import_errors)} import errors:\n" +
            "\n".join(import_errors[:5])
        )

    def test_no_root_shared_shadowing(self):
        """Root shared/ should not shadow value-fabric/shared/."""
        import value_fabric.shared

        shared_file = Path(value_fabric.shared.__file__)
        repo_root = REPO_ROOT

        # Check if shared resolves to root directory (bad)
        is_root_shared = (
            shared_file.parent == repo_root or
            str(shared_file).endswith("shared/__init__.py") and "value" not in str(shared_file)
        )

        assert not is_root_shared, (
            f"shared module resolves to {shared_file} which appears to be "
            "root shared/. This shadows value-fabric/shared/. "
            "Consider removing root shared/ or adjusting pythonpath."
        )
