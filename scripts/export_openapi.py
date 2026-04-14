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


def _load_module_isolated(module_name: str, module_path: Path) -> ModuleType:
    """Load a module in isolation, with guaranteed sys.modules cleanup.

    Args:
        module_name: Unique namespaced module name (e.g., 'layer1_ingestion.api.main')
        module_path: Path to the module file

    Returns:
        Loaded module object

    Raises:
        RuntimeError: If module cannot be loaded or spec/loader is invalid
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create import spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    original_module = sys.modules.get(module_name)

    try:
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        # Restore or remove module name to prevent cross-run contamination
        if original_module is not None:
            sys.modules[module_name] = original_module
        else:
            sys.modules.pop(module_name, None)


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

    # Pre-flight checks with structured context
    if not module_path.exists():
        logger.error(
            f"[{layer_name}] main.py not found",
            extra={"layer": layer_name, "path": str(module_path)},
        )
        return False

    # Minimal path injection: only layer root for src.* resolution
    original_path = sys.path.copy()
    injected_paths: list[str] = []

    base_str = str(base_path)
    if base_str not in sys.path:
        sys.path.insert(0, base_str)
        injected_paths.append(base_str)

    # Also inject shared root for shared.* imports if present
    shared_str = str(SHARED_ROOT)
    if shared_str not in sys.path:
        sys.path.insert(0, shared_str)
        injected_paths.append(shared_str)

    module_key = layer_dir.replace("-", "_")
    loaded_modules: list[str] = []

    try:
        logger.info(
            f"[{layer_name}] Loading module",
            extra={
                "layer": layer_name,
                "module_path": str(module_path),
                "injected_paths": injected_paths,
                "output_path": str(output_path),
            },
        )

        # Load main module with isolation
        main_module = _load_module_isolated(f"{module_key}.api.main", module_path)
        loaded_modules.append(f"{module_key}.api.main")

        # Load supporting package structure if exists
        src_init = src_path / "__init__.py"
        if src_init.exists():
            _load_module_isolated(module_key, src_init)
            loaded_modules.append(module_key)

        api_init = src_path / "api" / "__init__.py"
        if api_init.exists():
            _load_module_isolated(f"{module_key}.api", api_init)
            loaded_modules.append(f"{module_key}.api")

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
        logger.error(
            f"[{layer_name}] Export failed: {e}",
            extra={
                "layer": layer_name,
                "module_path": str(module_path),
                "injected_paths": injected_paths,
                "loaded_modules": loaded_modules,
            },
            exc_info=True,
        )
        return False

    finally:
        # Guaranteed cleanup: restore sys.path
        sys.path[:] = original_path


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
