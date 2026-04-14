#!/usr/bin/env python3
"""Export OpenAPI specifications from all Value Fabric layers.

Uses importlib for explicit module loading to avoid sys.path pollution.
Each layer is loaded in isolation with proper import context.
"""

import importlib.util
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Export directory
EXPORT_DIR = Path(__file__).parent.parent / "contracts" / "openapi"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Shared package root (for shared.* imports)
SHARED_ROOT = Path(__file__).parent.parent / "value-fabric"


def _setup_package_hierarchy(module_key: str, src_path: Path) -> list[str]:
    """Set up proper package hierarchy for relative imports.

    Creates parent packages in sys.modules with correct __path__ attributes
    to enable relative imports like `from ..config import ...`.

    Args:
        module_key: Package name (e.g., 'layer3_knowledge')
        src_path: Path to the src directory (package root)

    Returns:
        List of module names that were added to sys.modules
    """
    created_modules: list[str] = []

    # Create the root package (e.g., layer3_knowledge)
    if module_key not in sys.modules:
        root_spec = importlib.util.spec_from_file_location(
            module_key, src_path / "__init__.py", submodule_search_locations=[str(src_path)]
        )
        if root_spec:
            root_module = importlib.util.module_from_spec(root_spec)
            root_module.__path__ = [str(src_path)]  # type: ignore
            sys.modules[module_key] = root_module
            created_modules.append(module_key)

            # Load the root package to execute its imports
            if root_spec.loader:
                root_spec.loader.exec_module(root_module)

    # Create the api subpackage (e.g., layer3_knowledge.api)
    api_key = f"{module_key}.api"
    if api_key not in sys.modules:
        api_path = src_path / "api"
        api_init = api_path / "__init__.py"
        if api_init.exists():
            api_spec = importlib.util.spec_from_file_location(
                api_key, api_init, submodule_search_locations=[str(api_path)]
            )
            if api_spec:
                api_module = importlib.util.module_from_spec(api_spec)
                api_module.__path__ = [str(api_path)]  # type: ignore
                sys.modules[api_key] = api_module
                created_modules.append(api_key)

                # Set parent reference
                api_module.__package__ = module_key  # type: ignore

                if api_spec.loader:
                    api_spec.loader.exec_module(api_module)

    return created_modules


def _cleanup_modules(module_names: list[str]) -> None:
    """Remove created modules from sys.modules to prevent cross-layer contamination."""
    # Remove in reverse order (children before parents)
    for name in sorted(module_names, key=len, reverse=True):
        if name in sys.modules:
            del sys.modules[name]


def _load_main_module(module_key: str, module_path: Path) -> ModuleType:
    """Load the main.py module with proper package context.

    Args:
        module_key: Package name (e.g., 'layer3_knowledge')
        module_path: Path to api/main.py

    Returns:
        Loaded main module with working relative imports
    """
    full_name = f"{module_key}.api.main"

    spec = importlib.util.spec_from_file_location(full_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create import spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    module.__package__ = f"{module_key}.api"  # type: ignore
    sys.modules[full_name] = module
    spec.loader.exec_module(module)

    return module


def _atomic_write_json(data: dict[str, Any], output_path: Path) -> None:
    """Write JSON atomically using temp file + rename.

    Prevents partially written files on interrupt or failure.
    """
    # Write to temp file in same directory for atomic rename
    temp_fd, temp_path = tempfile.mkstemp(
        dir=output_path.parent, suffix=".tmp", prefix=output_path.stem
    )
    try:
        with os.fdopen(temp_fd, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename into place
        os.replace(temp_path, output_path)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _export_layer(layer_name: str, layer_dir: str, output_filename: str) -> bool:
    """Export OpenAPI spec for a single layer with full isolation.

    Args:
        layer_name: Human-readable layer name (for logging)
        layer_dir: Directory name under value-fabric/
        output_filename: Output JSON filename

    Returns:
        True if export succeeded, False otherwise
    """
    base_path = SHARED_ROOT / layer_dir
    src_path = base_path / "src"
    module_path = src_path / "api" / "main.py"
    output_path = EXPORT_DIR / output_filename

    # Pre-flight checks
    if not module_path.exists():
        logger.error(f"[{layer_name}] main.py not found at {module_path}")
        return False

    if not (src_path / "__init__.py").exists():
        logger.error(f"[{layer_name}] src/__init__.py missing - required for package structure")
        return False

    # Save original state for cleanup
    original_path = sys.path.copy()
    original_modules = set(sys.modules.keys())

    module_key = layer_dir.replace("-", "_")
    created_modules: list[str] = []

    try:
        # Add src to sys.path for top-level imports
        sys.path.insert(0, str(src_path))
        sys.path.insert(0, str(SHARED_ROOT))

        # Set up proper package hierarchy for relative imports
        created_modules = _setup_package_hierarchy(module_key, src_path)

        logger.info(f"[{layer_name}] Loading module from {module_path}")

        # Load main module with proper package context
        main_module = _load_main_module(module_key, module_path)
        created_modules.append(f"{module_key}.api.main")

        # Validate module shape
        app = getattr(main_module, "app", None)
        if app is None:
            raise RuntimeError(f"{module_path} does not define 'app'")

        # Validate FastAPI-like interface
        if not hasattr(app, "openapi") or not callable(app.openapi):
            raise RuntimeError(f"{module_path} 'app' does not have callable 'openapi()' method")

        # Generate and export spec atomically
        spec = app.openapi()
        _atomic_write_json(spec, output_path)

        logger.info(f"[OK] {layer_name} exported: {output_path}")
        return True

    except Exception as e:
        logger.error(f"[{layer_name}] Export failed: {e}", exc_info=True)
        return False

    finally:
        # Cleanup: restore sys.path
        sys.path[:] = original_path

        # Cleanup: remove all modules we created
        _cleanup_modules(created_modules)

        # Also remove any submodules that were loaded as side effects
        current_modules = set(sys.modules.keys())
        new_modules = current_modules - original_modules
        for name in new_modules:
            if name.startswith(module_key) or name.startswith("shared"):
                del sys.modules[name]


def export_layer1():
    """Export Layer 1 Ingestion OpenAPI spec."""
    return _export_layer("Layer 1", "layer1-ingestion", "layer1-ingestion.json")


def export_layer2():
    """Export Layer 2 Extraction OpenAPI spec."""
    return _export_layer("Layer 2", "layer2-extraction", "layer2-extraction.json")


def export_layer3():
    """Export Layer 3 Knowledge Graph OpenAPI spec."""
    return _export_layer("Layer 3", "layer3-knowledge", "layer3-knowledge.json")


def export_layer4():
    """Export Layer 4 Agentic Workflow Engine OpenAPI spec."""
    return _export_layer("Layer 4", "layer4-agents", "layer4-agents.json")


def main():
    """Export all OpenAPI specs."""
    print("Exporting Value Fabric OpenAPI specifications...")
    print(f"Export directory: {EXPORT_DIR}")
    print()

    results = {
        "layer1": export_layer1(),
        "layer2": export_layer2(),
        "layer3": export_layer3(),
        "layer4": export_layer4(),
    }

    print()
    success_count = sum(results.values())
    total_count = len(results)
    print(f"Exported {success_count}/{total_count} OpenAPI specifications")

    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
