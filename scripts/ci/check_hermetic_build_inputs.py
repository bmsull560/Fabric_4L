#!/usr/bin/env python3
"""Hard-fail policy checks for hermetic CI build inputs."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = [
    ROOT / ".github/workflows/build-deploy.yml",
    ROOT / ".github/workflows/supply-chain.yml",
    ROOT / ".github/workflows/pr-checks.yml",
    ROOT / ".github/workflows/critical-gates.yml",
]
DOCKERFILES = list((ROOT / "services").rglob("Dockerfile*")) + list((ROOT / "apps/web").glob("Dockerfile*"))
BUILD_SCRIPTS = list((ROOT / "scripts/ci").glob("*.sh")) + list((ROOT / "scripts/ci").glob("*.py")) + list((ROOT / ".github/scripts").glob("*.sh"))
APPROVED_DOMAINS = {
    "ghcr.io",
    "registry.value-fabric.internal",
    "localhost",
    "127.0.0.1",
}

ACTION_REF_RE = re.compile(r"^\s*-\s*uses:\s*([^@\s]+)@([^\s#]+)")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FROM_RE = re.compile(r"^\s*FROM\s+([^\s]+)", re.IGNORECASE)
URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")
RAW_DOMAIN_RE = re.compile(r"\b([a-z0-9.-]+\.[a-z]{2,})(?::\d+)?\b")

def domain_from_image(image: str) -> str:
    first = image.split("/", 1)[0]
    if "." not in first and ":" not in first:
        return "docker.io"
    return first


def check_workflows(violations: list[str]) -> None:
    for wf in WORKFLOWS:
        for i, line in enumerate(wf.read_text().splitlines(), start=1):
            m = ACTION_REF_RE.match(line)
            if not m:
                continue
            ref = m.group(2)
            if not SHA_RE.fullmatch(ref):
                violations.append(f"{wf.relative_to(ROOT)}:{i} unpinned action ref '{ref}'")


def check_dockerfiles(violations: list[str]) -> None:
    for dockerfile in DOCKERFILES:
        for i, line in enumerate(dockerfile.read_text().splitlines(), start=1):
            m = FROM_RE.match(line)
            if not m:
                continue
            image = m.group(1)
            if ":latest" in image or image.endswith(":latest"):
                violations.append(f"{dockerfile.relative_to(ROOT)}:{i} latest tag forbidden: {image}")
            if "@sha256:" not in image:
                violations.append(f"{dockerfile.relative_to(ROOT)}:{i} base image must be pinned by digest: {image}")
            domain = domain_from_image(image)
            if domain not in APPROVED_DOMAINS:
                violations.append(f"{dockerfile.relative_to(ROOT)}:{i} unapproved registry domain: {domain}")


def check_build_scripts(violations: list[str]) -> None:
    for script in BUILD_SCRIPTS:
        for i, line in enumerate(script.read_text().splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            for match in URL_RE.finditer(line):
                domain = match.group(1).lower()
                if domain == "...":
                    continue
                if domain not in APPROVED_DOMAINS:
                    violations.append(f"{script.relative_to(ROOT)}:{i} unapproved external URL domain: {domain}")
            if "docker pull " in line or "docker build " in line:
                for match in RAW_DOMAIN_RE.finditer(line):
                    domain = match.group(1).lower()
                    if domain not in APPROVED_DOMAINS:
                        violations.append(f"{script.relative_to(ROOT)}:{i} unapproved external domain in build context: {domain}")


def main() -> int:
    violations: list[str] = []
    check_workflows(violations)
    check_dockerfiles(violations)
    check_build_scripts(violations)

    if violations:
        print("Hermetic build input policy violations detected:")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("Hermetic build input policy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
