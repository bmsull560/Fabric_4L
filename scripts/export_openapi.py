#!/usr/bin/env python3
"""Export OpenAPI specifications from all Value Fabric layers."""

import json
import sys
from pathlib import Path

# Export directory
EXPORT_DIR = Path(__file__).parent.parent / "docs" / "openapi"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_layer3():
    """Export Layer 3 Knowledge Graph OpenAPI spec."""
    try:
        from value_fabric.layer3_knowledge.src.api.main import app
        spec = app.openapi()
        output_path = EXPORT_DIR / "layer3-knowledge.json"
        with open(output_path, "w") as f:
            json.dump(spec, f, indent=2)
        print(f"✓ Layer 3 exported: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Layer 3 export failed: {e}")
        return False


def export_layer5():
    """Export Layer 5 Ground Truth OpenAPI spec."""
    try:
        from value_fabric.layer5_ground_truth.src.api.main import app
        spec = app.openapi()
        output_path = EXPORT_DIR / "layer5-ground-truth.json"
        with open(output_path, "w") as f:
            json.dump(spec, f, indent=2)
        print(f"✓ Layer 5 exported: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Layer 5 export failed: {e}")
        return False


def export_layer6():
    """Export Layer 6 Benchmarks OpenAPI spec."""
    try:
        from value_fabric.layer6_benchmarks.src.api.main import app
        spec = app.openapi()
        output_path = EXPORT_DIR / "layer6-benchmarks.json"
        with open(output_path, "w") as f:
            json.dump(spec, f, indent=2)
        print(f"✓ Layer 6 exported: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Layer 6 export failed: {e}")
        return False


def main():
    """Export all OpenAPI specs."""
    print("Exporting Value Fabric OpenAPI specifications...")
    print(f"Export directory: {EXPORT_DIR}")
    print()

    results = {
        "layer3": export_layer3(),
        "layer5": export_layer5(),
        "layer6": export_layer6(),
    }

    print()
    success_count = sum(results.values())
    total_count = len(results)
    print(f"Exported {success_count}/{total_count} OpenAPI specifications")

    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
