#!/usr/bin/env python3
"""
Validate Dependabot Coverage (H-07 Audit Fix)

Ensures every package manifest and Dockerfile has:
1. A corresponding entry in dependabot.yml
2. An owner defined in CODEOWNERS

Exit codes:
    0 - All packages have coverage
    1 - Missing dependabot entries or CODEOWNERS ownership
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent

# File patterns that indicate a package needs dependabot coverage
PACKAGE_PATTERNS = {
    "pip": ["pyproject.toml", "requirements.txt", "setup.py"],
    "npm": ["package.json"],
    "docker": ["Dockerfile", "Dockerfile.*"],
}

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    ".tox",
    "archive",
    "dist",
    "build",
    ".next",
    "*.egg-info",
    "prototypes",  # Prototypes are temporary/experimental and don't need automated updates
}


def load_dependabot_config() -> Dict:
    """Load and parse dependabot.yml configuration."""
    config_path = REPO_ROOT / ".github" / "dependabot.yml"
    if not config_path.exists():
        print(f"::error::dependabot.yml not found at {config_path}")
        sys.exit(1)

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_codeowners() -> str:
    """Load CODEOWNERS file content."""
    codeowners_path = REPO_ROOT / ".github" / "CODEOWNERS"
    if not codeowners_path.exists():
        print(f"::error::CODEOWNERS not found at {codeowners_path}")
        sys.exit(1)

    with open(codeowners_path, "r") as f:
        return f.read()


def normalize_path(path: str) -> str:
    """Normalize path to use forward slashes and remove leading/trailing slashes."""
    return path.replace("\\", "/").strip("/")


def get_dependabot_entries(config: Dict) -> Dict[str, Set[str]]:
    """
    Extract dependabot entries by ecosystem.
    Returns: {ecosystem: set_of_directories}
    """
    entries = {"pip": set(), "npm": set(), "docker": set(), "github-actions": set()}

    for update in config.get("updates", []):
        ecosystem = update.get("package-ecosystem")
        directory = update.get("directory", "")

        if ecosystem in entries:
            # Normalize directory path (remove leading slash, ensure consistent format)
            normalized = normalize_path(directory)
            entries[ecosystem].add(normalized)

    return entries


def discover_packages() -> Dict[str, Set[Path]]:
    """
    Discover all packages in the repository by ecosystem.
    Returns: {ecosystem: set_of_package_paths}
    """
    packages = {"pip": set(), "npm": set(), "docker": set()}

    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip excluded directories
        dirs[:] = [
            d
            for d in dirs
            if d not in EXCLUDE_DIRS and not any(d.startswith(ex.lstrip("*")) for ex in EXCLUDE_DIRS if ex.startswith("*"))
        ]

        rel_root = Path(root).relative_to(REPO_ROOT)

        # Check for Python packages
        for pattern in PACKAGE_PATTERNS["pip"]:
            if pattern in files:
                packages["pip"].add(rel_root)
                break

        # Check for Node.js packages
        for pattern in PACKAGE_PATTERNS["npm"]:
            if pattern in files:
                packages["npm"].add(rel_root)
                break

        # Check for Dockerfiles
        for file in files:
            if file == "Dockerfile" or file.startswith("Dockerfile."):
                packages["docker"].add(rel_root)
                break

    return packages


def check_codeowners_ownership(codeowners: str, path_str: str) -> bool:
    """
    Check if a package path has an owner defined in CODEOWNERS.
    """
    # Check for exact match or parent directory match
    for line in codeowners.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse CODEOWNERS line: pattern owners...
        parts = line.split()
        if not parts:
            continue

        pattern = parts[0]
        owners = parts[1:]

        if not owners:
            continue

        # Remove leading slash from pattern for comparison
        pattern = pattern.lstrip("/")

        # Check if pattern matches the package path
        # Support glob patterns like **/Dockerfile or /apps/web/
        if pattern.endswith("/"):
            # Directory pattern
            prefix = pattern.rstrip("/")
            if path_str == prefix or path_str.startswith(prefix + "/"):
                return True
        elif pattern.startswith("**/"):
            # Glob pattern
            suffix = pattern[3:]
            if path_str.endswith(suffix) or suffix in path_str:
                return True
        elif pattern in path_str:
            return True

    return False


def validate_coverage(
    packages: Dict[str, Set[Path]], dependabot_entries: Dict[str, Set[str]], codeowners: str
) -> Tuple[List[str], List[str]]:
    """
    Validate that all packages have dependabot entries and CODEOWNERS ownership.
    Returns: (missing_dependabot, missing_ownership)
    """
    missing_dependabot = []
    missing_ownership = []

    for ecosystem, package_paths in packages.items():
        if ecosystem not in dependabot_entries:
            continue

        dependabot_dirs = dependabot_entries[ecosystem]

        for package_path in package_paths:
            path_str = normalize_path(str(package_path))

            # Check dependabot coverage
            if path_str not in dependabot_dirs:
                missing_dependabot.append(f"{ecosystem}: {path_str}")

            # Check CODEOWNERS ownership
            if not check_codeowners_ownership(codeowners, path_str):
                missing_ownership.append(f"{ecosystem}: {path_str}")

    return missing_dependabot, missing_ownership


def main():
    print("[SCAN] Validating Dependabot coverage and CODEOWNERS ownership...")
    print()

    # Load configurations
    print("Loading dependabot.yml...")
    dependabot_config = load_dependabot_config()

    print("Loading CODEOWNERS...")
    codeowners = load_codeowners()

    # Extract dependabot entries
    dependabot_entries = get_dependabot_entries(dependabot_config)
    print()
    print("Dependabot configured entries:")
    for ecosystem, dirs in dependabot_entries.items():
        print(f"  {ecosystem}: {len(dirs)} entries")
        for d in sorted(dirs):
            print(f"    - {d}")

    # Discover packages
    print()
    print("Discovering packages...")
    packages = discover_packages()
    print(f"  pip packages: {len(packages['pip'])}")
    print(f"  npm packages: {len(packages['npm'])}")
    print(f"  docker packages: {len(packages['docker'])}")

    for ecosystem, paths in packages.items():
        if paths:
            print(f"\n  {ecosystem} paths:")
            for p in sorted(paths):
                print(f"    - {p}")

    # Validate coverage
    print()
    print("Validating coverage...")
    missing_dependabot, missing_ownership = validate_coverage(
        packages, dependabot_entries, codeowners
    )

    # Report results
    exit_code = 0

    if missing_dependabot:
        print()
        print("::error::Missing dependabot.yml entries:")
        for item in missing_dependabot:
            print(f"  [FAIL] {item}")
        exit_code = 1
    else:
        print()
        print("[PASS] All packages have dependabot.yml entries")

    if missing_ownership:
        print()
        print("::error::Missing CODEOWNERS ownership:")
        for item in missing_ownership:
            print(f"  [FAIL] {item}")
        exit_code = 1
    else:
        print()
        print("[PASS] All packages have CODEOWNERS ownership")

    # Summary
    print()
    print("=" * 60)
    if exit_code == 0:
        print("[SUCCESS] VALIDATION PASSED")
        print("All package manifests and Dockerfiles have update owners.")
    else:
        print("[ERROR] VALIDATION FAILED")
        print("Some packages are missing dependabot coverage or ownership.")
    print("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
