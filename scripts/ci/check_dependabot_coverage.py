#!/usr/bin/env python3
"""Validate that every active package manifest and Dockerfile has a Dependabot entry.

Exits non-zero and prints a report if any manifest or Dockerfile directory is
not covered by .github/dependabot.yml.

Usage:
    python scripts/ci/check_dependabot_coverage.py
    python scripts/ci/check_dependabot_coverage.py --root /path/to/repo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Directories to exclude from discovery.
#
# Add a directory here when it intentionally has no Dependabot entry:
#   - Legacy/obsolete roots (value-fabric, frontend) — moved to services/ and apps/
#   - Test fixture files (tests/) — requirements.txt there is a test helper,
#     not a deployable package; its deps are covered by the service entries
#   - Generated/tooling dirs — devcontainer, prototypes, archive
# ---------------------------------------------------------------------------
EXCLUDE_DIRS = frozenset(
    [
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        # Legacy / obsolete roots — moved to services/ and apps/
        "value-fabric",
        "frontend",
        "archive",
        "prototypes",
        # Devcontainer — base image managed separately from application images
        ".devcontainer",
        # Test fixture requirements — not a deployable package
        "tests",
    ]
)

# Manifest filenames that indicate a pip-managed directory
PIP_MANIFESTS = {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"}

# Manifest filenames that indicate an npm-managed directory
NPM_MANIFESTS = {"package.json"}


def _excluded(path: Path, root: Path) -> bool:
    """Return True if any component of path (relative to root) is in EXCLUDE_DIRS."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def discover_pip_dirs(root: Path) -> set[str]:
    """Return repo-relative directory paths that contain a pip manifest."""
    dirs: set[str] = set()
    for name in PIP_MANIFESTS:
        for p in root.rglob(name):
            if _excluded(p, root):
                continue
            rel = "/" + str(p.parent.relative_to(root))
            dirs.add(rel)
    return dirs


def discover_npm_dirs(root: Path) -> set[str]:
    """Return repo-relative directory paths that contain a package.json.

    Skips package.json files that are clearly not workspace roots
    (e.g. inside a dist/ or build/ subdirectory).
    """
    skip_parents = {"dist", "build", ".next", "coverage", "out"}
    dirs: set[str] = set()
    for p in root.rglob("package.json"):
        if _excluded(p, root):
            continue
        if any(part in skip_parents for part in p.parts):
            continue
        rel = "/" + str(p.parent.relative_to(root))
        dirs.add(rel)
    return dirs


def discover_docker_dirs(root: Path) -> set[str]:
    """Return repo-relative directory paths that contain a Dockerfile."""
    dirs: set[str] = set()
    for p in root.rglob("Dockerfile*"):
        if _excluded(p, root):
            continue
        # Only match files named exactly Dockerfile or Dockerfile.<suffix>
        if not (p.name == "Dockerfile" or p.name.startswith("Dockerfile.")):
            continue
        rel = "/" + str(p.parent.relative_to(root))
        dirs.add(rel)
    return dirs


def load_dependabot_entries(dependabot_path: Path) -> dict[str, set[str]]:
    """Parse dependabot.yml and return {ecosystem: {directory, ...}}."""
    data = yaml.safe_load(dependabot_path.read_text()) or {}
    covered: dict[str, set[str]] = {}
    for entry in data.get("updates", []):
        ecosystem = entry.get("package-ecosystem", "")
        directory = entry.get("directory", "")
        covered.setdefault(ecosystem, set()).add(directory)
    return covered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root (default: two levels above this script)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    dependabot_path = root / ".github" / "dependabot.yml"

    if not dependabot_path.exists():
        print(f"ERROR: {dependabot_path} not found", file=sys.stderr)
        return 1

    covered = load_dependabot_entries(dependabot_path)
    pip_covered = covered.get("pip", set())
    npm_covered = covered.get("npm", set())
    docker_covered = covered.get("docker", set())

    pip_dirs = discover_pip_dirs(root)
    npm_dirs = discover_npm_dirs(root)
    docker_dirs = discover_docker_dirs(root)

    missing_pip = sorted(pip_dirs - pip_covered)
    missing_npm = sorted(npm_dirs - npm_covered)
    missing_docker = sorted(docker_dirs - docker_covered)

    # Report
    ok = True

    if missing_pip:
        ok = False
        print("pip manifests with no Dependabot entry:")
        for d in missing_pip:
            print(f"  {d}  (add pip entry for directory: {d})")

    if missing_npm:
        ok = False
        print("npm manifests with no Dependabot entry:")
        for d in missing_npm:
            print(f"  {d}  (add npm entry for directory: {d})")

    if missing_docker:
        ok = False
        print("Dockerfile directories with no Dependabot entry:")
        for d in missing_docker:
            print(f"  {d}  (add docker entry for directory: {d})")

    if ok:
        total = len(pip_dirs) + len(npm_dirs) + len(docker_dirs)
        print(
            f"dependabot coverage OK — {len(pip_dirs)} pip, "
            f"{len(npm_dirs)} npm, {len(docker_dirs)} docker "
            f"({total} total manifest locations covered)"
        )
        return 0

    print(
        "\nUpdate .github/dependabot.yml to add the missing entries above.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
