#!/usr/bin/env python3
"""Production auth bypass prevention gate.

Scans production-like deployment manifests for insecure authentication bypass
flags and weak defaults that could silently disable auth in staging/prod.
"""

from __future__ import annotations

from pathlib import Path
import sys

BYPASS_FLAGS = (
    "DEV_AUTH_BYPASS",
    "ALLOW_INSECURE_DEV_AUTH_BYPASS",
    "ALLOW_DEV_AUTH_BYPASS",
    "AUTH_BYPASS_ENABLED",
)

WEAK_PATTERNS = (
    'VITE_ENABLE_MOCK_FALLBACK: "true"',
    "VITE_ENABLE_MOCK_FALLBACK: true",
    "dev-local-secret-do-not-use-in-production",
    "dev-local-service-auth-secret",
)

SCAN_ROOTS = (
    Path("k8s/envs/prod"),
    Path("k8s/envs/staging"),
    Path("k8s/deployments/prod-gateway-api"),
    Path("k8s/deployments/prod-istio"),
    Path("k8s/deployments/prod-nginx"),
)

EXPLICIT_FILES = (
    Path("docker-compose.live.yml"),
    Path("docker-compose.full.yml"),
)


def yaml_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([*root.rglob("*.yml"), *root.rglob("*.yaml")])


def main() -> int:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        files.extend(yaml_files(root))
    files.extend([p for p in EXPLICIT_FILES if p.exists()])

    errors: list[str] = []
    for path in sorted(set(files)):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            normalized = line.strip().lower()
            for flag in BYPASS_FLAGS:
                if flag in line and any(tok in normalized for tok in ("true", "i_understand_risk")):
                    errors.append(
                        f"{path}:{line_no} contains forbidden bypass flag assignment: {line.strip()}"
                    )
            for pattern in WEAK_PATTERNS:
                if pattern in line:
                    errors.append(f"{path}:{line_no} contains insecure pattern: {pattern}")

    if errors:
        print("ERROR: Production auth bypass check failed.\n")
        for error in errors:
            print(f" - {error}")
        print("\nRemove bypass flags and weak defaults from production/staging overlays and manifests.")
        return 1

    print("Production auth bypass check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
