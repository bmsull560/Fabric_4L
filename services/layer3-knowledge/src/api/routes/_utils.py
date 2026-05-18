"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Shared utilities for API routes.

Common helpers for validation, parsing, and formatting.
"""

import re


def parse_semver(version: str) -> tuple[int, int, int, str | None, str | None]:
    """Parse semver string into components.

    Returns: (major, minor, patch, prerelease, build_metadata)
    Handles: 1.2.3, 1.2.3-beta, 1.2.3+build, 1.2.3-beta+build
    """
    # Remove build metadata first
    build = None
    if "+" in version:
        version, build = version.rsplit("+", 1)

    # Extract prerelease
    prerelease = None
    if "-" in version:
        version, prerelease = version.split("-", 1)

    # Parse core version
    parts = version.split(".")
    try:
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return (0, 0, 0, prerelease, build)

    return (major, minor, patch, prerelease, build)


def semver_key(version: str) -> tuple[int, int, int]:
    """Convert semver to sortable tuple (ignores prerelease/build).

    Invalid versions sort to (0, 0, 0).
    """
    major, minor, patch, _, _ = parse_semver(version)
    return (major, minor, patch)


def is_valid_semver(version: str) -> bool:
    """Validate semver format (X.Y.Z[-prerelease][+build])."""
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$"
    return bool(re.match(pattern, version))


def increment_patch_version(version: str) -> str:
    """Increment patch version, preserving prerelease/build format.

    Examples:
        1.2.3 -> 1.2.4
        1.2.3-beta -> 1.2.4-beta
        1.0 -> 1.0.1 (handles partial versions)
    """
    major, minor, patch, prerelease, build = parse_semver(version)

    # Construct new version
    new_version = f"{major}.{minor}.{patch + 1}"
    if prerelease:
        new_version += f"-{prerelease}"
    if build:
        new_version += f"+{build}"

    return new_version
