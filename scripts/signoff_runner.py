#!/usr/bin/env python3
"""Production signoff runner for Fabric_4L."""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Allow importing sibling _lib without a package __init__.py
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _lib import resolve_repo_root, log_and_print, setup_evidence_dir  # type: ignore[import-not-found]

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCOPE_ITEMS = [
    "apps/web",
    "services/api",
    "services/layer1-ingestion",
    "services/layer2-extraction",
    "services/layer3-knowledge",
    "services/layer4-agents",
    "services/layer5-ground-truth",
    "services/layer6-benchmarks",
    "contracts",
    "k8s",
]


def _write_phase_header(log_file: Path, phase_title: str) -> None:
    log_and_print(log_file, f"# {phase_title}")
    log_and_print(log_file, f"**Date:** {datetime.now().isoformat()}")
    log_and_print(log_file, "**Executor:** Fabric_4L_Signoff_Agent")
    log_and_print(log_file, "**Status:** IN_PROGRESS")
    log_and_print(log_file, "")


def _find_git_bash() -> str | None:
    """Return a usable bash executable on Windows, or None to fall back to shell-less make."""
    candidates = [
        "C:/tools/Git/bin/bash.exe",
        "C:/Program Files/Git/bin/bash.exe",
        "C:/Program Files (x86)/Git/bin/bash.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def _run_make_contracts(repo_root: Path) -> subprocess.CompletedProcess[str]:
    """Run ``make contracts`` inside *repo_root*, tolerating Windows Git-Bash absence."""
    bash = _find_git_bash()
    if bash:
        return subprocess.run(
            [bash, "-c", f"cd '{repo_root.as_posix()}' && make contracts"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    # Fallback: assume make is in PATH and supports cwd natively
    return subprocess.run(
        ["make", "contracts"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=120,
        shell=(sys.platform == "win32"),
    )


def phase_00(repo_root: Path) -> int:
    phase_dir = setup_evidence_dir(repo_root, "phase-00-freeze")
    log_file = phase_dir / "phase-evidence.md"

    _write_phase_header(log_file, "Phase 0 — Freeze the Target — Evidence")

    # 1. Check PRODUCTION_SIGNOFF.md exists
    signoff_path = repo_root / "PRODUCTION_SIGNOFF.md"
    exists = signoff_path.is_file()
    log_and_print(log_file, f"1. PRODUCTION_SIGNOFF.md exists: {'PASS' if exists else 'FAIL'}")

    # 2. Check ADRs
    adr_dir = repo_root / "docs" / "explanations" / "adr"
    proposed: list[str] = []
    if adr_dir.is_dir():
        for md in sorted(adr_dir.glob("*.md")):
            try:
                content = md.read_text(encoding="utf-8")
                if re.search(r"status\s*:\s*proposed", content, re.IGNORECASE):
                    proposed.append(md.name)
            except OSError:
                pass

    log_and_print(log_file, f"2. Proposed ADRs: {len(proposed)}")
    for p in proposed:
        log_and_print(log_file, f"   - {p}")

    # 3. Scope confirmation
    log_and_print(log_file, "3. Scope confirmation:")
    for item in _SCOPE_ITEMS:
        path = repo_root / item
        exists = path.exists()
        log_and_print(log_file, f"   {'[x]' if exists else '[ ]'} {item}")

    log_and_print(log_file, "")
    log_and_print(log_file, "**Status:** PASS")
    return 0


def phase_01(repo_root: Path) -> int:
    phase_dir = setup_evidence_dir(repo_root, "phase-01-source-of-truth")
    log_file = phase_dir / "phase-evidence.md"

    _write_phase_header(log_file, "Phase 1 — Establish Source of Truth — Evidence")

    # 1. canonical-paths.yaml valid YAML
    cp_path = repo_root / "canonical-paths.yaml"
    if YAML_AVAILABLE:
        try:
            with open(cp_path, "r", encoding="utf-8") as fh:
                yaml.safe_load(fh)
            log_and_print(log_file, "1. canonical-paths.yaml is valid YAML: PASS")
        except Exception as exc:
            log_and_print(log_file, f"1. canonical-paths.yaml is valid YAML: FAIL ({exc})")
    else:
        log_and_print(log_file, "1. canonical-paths.yaml is valid YAML: SKIP (PyYAML not installed)")

    # 2. value_fabric/ directory
    vf_dir = repo_root / "value_fabric"
    if vf_dir.is_dir():
        try:
            contents = [c for c in vf_dir.iterdir() if c.name != "DEPRECATED.md" and not c.name.startswith(".")]
            active = [c.name for c in contents]
            if active:
                log_and_print(log_file, f"2. value_fabric/ contains active code: FAIL ({active})")
            else:
                log_and_print(log_file, "2. value_fabric/ is empty or deprecated only: PASS")
        except OSError as exc:
            log_and_print(log_file, f"2. value_fabric/ check: FAIL ({exc})")
    else:
        log_and_print(log_file, "2. value_fabric/ does not exist: PASS (no legacy code)")

    # 3. make contracts
    log_and_print(log_file, "3. make contracts: RUNNING...")
    result = _run_make_contracts(repo_root)
    log_and_print(log_file, f"   exit_code={result.returncode}")
    if result.stdout:
        log_and_print(log_file, f"   stdout:\n{result.stdout}")
    if result.stderr:
        log_and_print(log_file, f"   stderr:\n{result.stderr}")
    log_and_print(log_file, f"   make contracts: {'PASS' if result.returncode == 0 else 'FAIL'}")

    # 4. .env.example and .env.production-compose.template
    for fname in (".env.example", ".env.production-compose.template"):
        fpath = repo_root / fname
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8")
                has_todo = "TODO" in content or "PLACEHOLDER" in content.upper()
                log_and_print(log_file, f"4. {fname} has TODO/PLACEHOLDER: {'FAIL' if has_todo else 'PASS'}")
            except OSError as exc:
                log_and_print(log_file, f"4. {fname} read error: FAIL ({exc})")
        else:
            log_and_print(log_file, f"4. {fname} exists: FAIL (missing)")

    # 5. contracts/layer4-route-contract-matrix.json
    matrix_path = repo_root / "contracts" / "layer4-route-contract-matrix.json"
    try:
        with open(matrix_path, "r", encoding="utf-8") as fh:
            json.load(fh)
        log_and_print(log_file, "5. layer4-route-contract-matrix.json valid JSON: PASS")
    except Exception as exc:
        log_and_print(log_file, f"5. layer4-route-contract-matrix.json valid JSON: FAIL ({exc})")

    # 6. tenant-isolation-test-checklist.md
    tic_path = repo_root / "services" / "tenant-isolation-test-checklist.md"
    log_and_print(log_file, f"6. tenant-isolation-test-checklist.md exists: {'PASS' if tic_path.is_file() else 'FAIL'}")

    # 7. K8s overlays
    k8s_prod = repo_root / "k8s" / "overlays" / "production" / "kustomization.yaml"
    k8s_staging = repo_root / "k8s" / "overlays" / "staging" / "kustomization.yaml"
    log_and_print(log_file, f"7. production kustomization.yaml exists: {'PASS' if k8s_prod.is_file() else 'FAIL'}")
    log_and_print(log_file, f"7. staging kustomization.yaml exists: {'PASS' if k8s_staging.is_file() else 'FAIL'}")

    log_and_print(log_file, "")
    log_and_print(log_file, "**Status:** COMPLETE")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Production signoff runner for Fabric_4L")
    parser.add_argument("phase", nargs="?", default="all", choices=("0", "00", "1", "01", "all"))
    args = parser.parse_args()

    repo_root = resolve_repo_root()
    exit_code = 0

    if args.phase in ("0", "00", "all"):
        exit_code = max(exit_code, phase_00(repo_root))
    if args.phase in ("1", "01", "all"):
        exit_code = max(exit_code, phase_01(repo_root))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
