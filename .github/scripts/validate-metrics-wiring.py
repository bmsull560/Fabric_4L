#!/usr/bin/env python3
"""
Validate Prometheus metrics wiring for Layers 2–6.

This script ensures that all layers with prometheus_metrics.py modules
also properly expose a /metrics endpoint and initialize metrics during startup.

Exit codes:
    0: All layers properly wired
    1: One or more layers have incomplete metrics wiring
"""

import re
import sys
from pathlib import Path


def get_layer_paths(layer: int) -> tuple[Path, Path]:
    """Get paths to main.py and prometheus_metrics.py for a layer."""
    base = Path("value-fabric")

    layer_dirs = {
        2: "layer2-extraction/src/layer2_extraction",
        3: "layer3-knowledge/src",
        4: "layer4-agents/src",
        5: "layer5-ground-truth/src/layer5_ground_truth",
        6: "layer6-benchmarks/src",
    }

    metrics_dirs = {
        2: "layer2-extraction/src/layer2_extraction",
        3: "layer3-knowledge/src",
        4: "layer4-agents/src",
        5: "layer5-ground-truth/src",
        6: "layer6-benchmarks/src",
    }

    main_file = base / layer_dirs[layer] / "api" / "main.py"
    metrics_file = base / metrics_dirs[layer] / "metrics" / "prometheus_metrics.py"

    return main_file, metrics_file


def check_layer(layer: int) -> dict:
    """Check if a layer has complete metrics wiring."""
    main_file, metrics_file = get_layer_paths(layer)

    result = {
        "layer": layer,
        "has_metrics_module": metrics_file.exists(),
        "has_main": main_file.exists(),
        "has_init_metrics": False,
        "has_metrics_endpoint": False,
        "has_get_metrics": False,
        "errors": [],
    }

    if not main_file.exists():
        result["errors"].append(f"main.py not found at {main_file}")
        return result

    content = main_file.read_text(encoding="utf-8")

    # Also check router files for /metrics endpoints
    routes_dir = main_file.parent / "routes"
    if routes_dir.exists():
        for route_file in routes_dir.glob("*.py"):
            try:
                content += route_file.read_text(encoding="utf-8")
            except Exception:
                pass

    # Check for initialize_metrics import or usage
    result["has_init_metrics"] = "initialize_metrics" in content

    # Check for /metrics endpoint (various patterns across layers)
    # Pattern 1: @app.get("/metrics" or @app.get(\n    "/metrics"
    # Pattern 2: @router.get("/metrics")
    # Pattern 3: app.mount("/metrics"
    result["has_metrics_endpoint"] = bool(
        re.search(r'@app\.(get|mount)\s*\(\s*["\']?/metrics', content)
        or re.search(r'@router\.get\s*\(\s*["\']?/metrics', content)
        or re.search(r'app\.mount\s*\(\s*["\']?/metrics', content)
        or '"path": "/metrics"' in content
    )

    # Check for get_metrics usage (for health check integration)
    result["has_get_metrics"] = "get_metrics()" in content

    # Validate consistency
    if result["has_metrics_module"]:
        if not result["has_init_metrics"]:
            result["errors"].append("has prometheus_metrics.py but does not call initialize_metrics()")
        if not result["has_metrics_endpoint"]:
            result["errors"].append("has prometheus_metrics.py but does not expose /metrics endpoint")
        if not result["has_get_metrics"]:
            result["errors"].append("has prometheus_metrics.py but does not use get_metrics() in health check")

    return result


def main() -> int:
    """Main validation function."""
    print("=" * 70)
    print("Prometheus Metrics Wiring Validation")
    print("=" * 70)
    print()

    layers = [2, 3, 4, 5, 6]
    results = [check_layer(layer) for layer in layers]

    errors_found = []

    for result in results:
        layer = result["layer"]
        has_module = result["has_metrics_module"]
        is_wired = result["has_init_metrics"] and result["has_metrics_endpoint"]

        if has_module and is_wired:
            status = "OK"
        elif not has_module:
            status = "NO MODULE"
        else:
            status = "INCOMPLETE"
            errors_found.extend([f"Layer {layer}: {e}" for e in result["errors"]])

        print(f"Layer {layer}: {status}")
        if result["errors"]:
            for error in result["errors"]:
                print(f"  - {error}")

    print()
    print("=" * 70)

    if errors_found:
        print("FAIL: Metrics wiring incomplete")
        print()
        for error in errors_found:
            print(f"  - {error}")
        return 1
    else:
        print("PASS: All layers with metrics modules are properly wired")
        return 0


if __name__ == "__main__":
    sys.exit(main())
