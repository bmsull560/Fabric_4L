"""Duplicate source-tree drift gate.

Scans ``value_fabric/layer*/`` for ``.py`` files that also exist under the
corresponding ``services/layer*-*/src/`` tree.  Any duplicate file is a
regression risk: a fix applied to one tree may not reach the other.

Exit codes
----------
0  – no duplicates detected
1  – one or more duplicate files found
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Map value_fabric/layerN/ prefix -> services/layerN-foo/src/ prefix
LAYER_MAP: dict[str, str] = {
    "layer1": "services/layer1-ingestion/src",
    "layer2": "services/layer2-extraction/src",
    "layer3": "services/layer3-knowledge/src",
    "layer4": "services/layer4-agents/src",
}

# __init__.py files under this size are considered redirect shims, not duplicates
SHIM_MAX_BYTES: int = 1024


def _files_equal(a: Path, b: Path) -> bool:
    """Return True if two files have identical contents."""
    try:
        a_content = a.read_text(encoding="utf-8")
        b_content = b.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        a_content = a.read_bytes()
        b_content = b.read_bytes()
    return a_content == b_content


def find_duplicates(
    *, layer_map: dict[str, str] | None = None, strict: bool = False
) -> list[tuple[Path, Path]]:
    """Return list of (vf_path, svc_path) pairs that are duplicates."""
    duplicates: list[tuple[Path, Path]] = []
    layer_map = layer_map or LAYER_MAP

    for layer_name, svc_rel in layer_map.items():
        vf_dir = REPO_ROOT / "value_fabric" / layer_name
        svc_dir = REPO_ROOT / svc_rel

        if not vf_dir.exists() or not svc_dir.exists():
            continue

        for vf_file in vf_dir.rglob("*.py"):
            # Skip redirect-shim __init__.py files (single-file packages)
            if vf_file.name == "__init__.py" and vf_file.stat().st_size < SHIM_MAX_BYTES:
                continue

            rel = vf_file.relative_to(vf_dir)
            svc_file = svc_dir / rel

            if svc_file.exists():
                if strict:
                    # In strict mode, any co-existing file is a violation
                    duplicates.append((vf_file, svc_file))
                elif _files_equal(vf_file, svc_file):
                    duplicates.append((vf_file, svc_file))

    return duplicates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="flag any co-existing file, even if contents differ",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON summary",
    )
    parser.add_argument(
        "--layers",
        nargs="+",
        choices=list(LAYER_MAP.keys()),
        default=list(LAYER_MAP.keys()),
        help="which layers to scan (default: all layers)",
    )
    args = parser.parse_args(argv)

    # Restrict scan to requested layers
    layer_map = {k: v for k, v in LAYER_MAP.items() if k in args.layers}
    duplicates = find_duplicates(layer_map=layer_map, strict=args.strict)

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "pass": len(duplicates) == 0,
                    "violations": [
                        {
                            "value_fabric": str(d[0].relative_to(REPO_ROOT).as_posix()),
                            "service": str(d[1].relative_to(REPO_ROOT).as_posix()),
                        }
                        for d in duplicates
                    ],
                }
            )
        )
    else:
        if duplicates:
            print("ERROR: Duplicate source-tree files detected:", file=sys.stderr)
            for vf_file, svc_file in duplicates:
                print(
                    f"  {vf_file.relative_to(REPO_ROOT)}"
                    f"  ==  {svc_file.relative_to(REPO_ROOT)}",
                    file=sys.stderr,
                )
            print(
                f"\nFound {len(duplicates)} duplicate file(s). "
                "Remove the copy under value_fabric/layer*/ and keep the canonical tree "
                "under services/layer*-*/src/.",
                file=sys.stderr,
            )
        else:
            print("No duplicate source-tree files detected.")

    return 1 if duplicates else 0


if __name__ == "__main__":
    sys.exit(main())
