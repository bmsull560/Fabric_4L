#!/usr/bin/env python3
"""Repository-owned contract freshness and compatibility gate.

This script is the single CI/local entrypoint for contract-compliance checks:

1. Regenerate OpenAPI specs and fail if committed artifacts drift.
2. Regenerate generated TypeScript artifacts and fail if committed artifacts drift.
3. Typecheck frontend consumers for the touched API surfaces (fast mode) or the
   full frontend workspace (full mode).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "apps" / "web"
OPENAPI_ROOT = REPO_ROOT / "contracts" / "openapi"
PLATFORM_GENERATED_ROOT = REPO_ROOT / "packages" / "platform-contract" / "src" / "typescript" / "generated"
WEB_GENERATED_ROOT = WEB_ROOT / "src" / "api" / "generated"

ALL_SPECS = (
    "layer1-ingestion.json",
    "layer2-extraction.json",
    "layer3-knowledge.json",
    "layer4-agents.json",
    "layer5-ground-truth.json",
    "layer6-benchmarks.json",
    "signals.json",
)

LAYER_CONFIG = {
    "layer1-ingestion.json": {
        "service_prefixes": ("services/layer1-ingestion/", "value_fabric/layer1/"),
        "platform_file": "layer1_ingestion.ts",
        "web_dir": "l1",
        "import_alias": "l1",
    },
    "layer2-extraction.json": {
        "service_prefixes": ("services/layer2-extraction/", "value_fabric/layer2/"),
        "platform_file": "layer2_extraction.ts",
        "web_dir": "l2",
        "import_alias": "l2",
    },
    "layer3-knowledge.json": {
        "service_prefixes": ("services/layer3-knowledge/", "value_fabric/layer3/"),
        "platform_file": "layer3_knowledge.ts",
        "web_dir": "l3",
        "import_alias": "l3",
    },
    "layer4-agents.json": {
        "service_prefixes": ("services/layer4-agents/", "value_fabric/layer4/"),
        "platform_file": "layer4_agents.ts",
        "web_dir": "l4",
        "import_alias": "l4",
    },
    "layer5-ground-truth.json": {
        "service_prefixes": (
            "services/layer5-ground-truth/",
            "services/layer5-ground-truth/src/layer5_ground_truth/",
            "value_fabric/layer5/",
        ),
        "platform_file": "layer5_ground_truth.ts",
        "web_dir": "l5",
        "import_alias": "l5",
    },
    "layer6-benchmarks.json": {
        "service_prefixes": ("services/layer6-benchmarks/", "value_fabric/layer6/"),
        "platform_file": "layer6_benchmarks.ts",
        "web_dir": "l6",
        "import_alias": "l6",
    },
    "signals.json": {
        "service_prefixes": ("services/signals/", "value_fabric/signals/"),
        "platform_file": "signals.ts",
        "web_dir": "signals",
        "import_alias": "signals",
    },
}

FORCE_FULL_PREFIXES = (
    ".github/workflows/contract-compliance.yml",
    ".github/workflows/generated-api-freshness.yml",
    "scripts/export_openapi.py",
    "scripts/ci/contract_compliance_gate.py",
    "packages/platform-contract/scripts/generate-openapi-types.mjs",
    "apps/web/scripts/generate-api-types.ts",
    "package.json",
    "pnpm-lock.yaml",
)

TS_FILE_SUFFIXES = (".ts", ".tsx")
TS_EXCLUDE_TOKENS = (".test.", ".spec.")


def _print_header(title: str) -> None:
    print(f"\n== {title} ==")


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    printable_cwd = str(cwd or REPO_ROOT)
    print(f"$ ({printable_cwd}) {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )
    if capture:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def _git_changed_files(base_ref: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_ref}...HEAD", "--"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"Could not diff against base ref '{base_ref}'. Falling back to full mode.",
            file=sys.stderr,
        )
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _detect_touched_specs(changed_files: list[str]) -> tuple[str, ...]:
    if not changed_files:
        return ALL_SPECS

    if any(path.startswith(prefix) for path in changed_files for prefix in FORCE_FULL_PREFIXES):
        return ALL_SPECS

    touched: list[str] = []
    for path in changed_files:
        normalized = path.replace("\\", "/")
        for spec_name, config in LAYER_CONFIG.items():
            if normalized == f"contracts/openapi/{spec_name}":
                touched.append(spec_name)
                break
            if normalized == f"packages/platform-contract/src/typescript/generated/{config['platform_file']}":
                touched.append(spec_name)
                break
            if normalized == f"apps/web/src/api/generated/{config['web_dir']}/index.ts":
                touched.append(spec_name)
                break
            if any(normalized.startswith(prefix) for prefix in config["service_prefixes"]):
                touched.append(spec_name)
                break

    if not touched:
        return ALL_SPECS

    seen: dict[str, None] = {}
    for spec_name in touched:
        seen.setdefault(spec_name, None)
    return tuple(seen.keys())


def _selected_diff_paths(specs: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for spec_name in specs:
        config = LAYER_CONFIG[spec_name]
        paths.append(f"contracts/openapi/{spec_name}")
        paths.append(f"packages/platform-contract/src/typescript/generated/{config['platform_file']}")
        paths.append(f"apps/web/src/api/generated/{config['web_dir']}/index.ts")
    paths.append("packages/platform-contract/src/typescript/generated/index.ts")
    paths.append("apps/web/src/api/generated/index.ts")
    return paths


def _validate_json_artifacts(specs: Iterable[str]) -> None:
    _print_header("Validate OpenAPI JSON")
    for spec_name in specs:
        spec_path = OPENAPI_ROOT / spec_name
        if not spec_path.exists() or spec_path.stat().st_size == 0:
            raise SystemExit(f"Missing or empty OpenAPI contract: {spec_path}")
        with spec_path.open("r", encoding="utf-8") as handle:
            json.load(handle)
        print(f"Validated {spec_path.relative_to(REPO_ROOT)}")


def _check_diff(paths: list[str], *, failure_heading: str, failure_help: list[str]) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", *paths],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not changed:
        print(f"{failure_heading}: clean")
        return

    print(f"{failure_heading}: drift detected", file=sys.stderr)
    for path in changed:
        print(f"  - {path}", file=sys.stderr)
    print("", file=sys.stderr)
    for line in failure_help:
        print(line, file=sys.stderr)
    raise SystemExit(1)


def _regenerate_openapi(specs: tuple[str, ...]) -> None:
    _print_header("Regenerate OpenAPI")
    _run(["python", "scripts/export_openapi.py", "--only", *specs], cwd=REPO_ROOT)
    _validate_json_artifacts(specs)


def _regenerate_types(specs: tuple[str, ...]) -> None:
    _print_header("Regenerate TypeScript Types")
    command = ["node", "packages/platform-contract/scripts/generate-openapi-types.mjs"]
    for spec_name in specs:
        command.extend(["--spec", spec_name])
    _run(command, cwd=REPO_ROOT)


def _iter_web_source_files() -> Iterable[Path]:
    for root_name in ("src", "shared", "server"):
        root = WEB_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in TS_FILE_SUFFIXES:
                continue
            if any(token in path.name for token in TS_EXCLUDE_TOKENS):
                continue
            yield path


def _collect_targeted_typecheck_files(specs: Iterable[str]) -> list[str]:
    touched_aliases = {LAYER_CONFIG[spec_name]["import_alias"] for spec_name in specs}
    files: list[str] = []
    direct_imports = tuple(f"@/api/generated/{alias}" for alias in touched_aliases)

    for path in _iter_web_source_files():
        text = path.read_text(encoding="utf-8")
        if any(direct_import in text for direct_import in direct_imports):
            files.append(path.relative_to(WEB_ROOT).as_posix())
            continue
        if "@/api/generated" not in text:
            continue
        for alias in touched_aliases:
            pattern = re.compile(
                rf"import\s+(?:type\s+)?{{[^}}]*\b{re.escape(alias)}\b[^}}]*}}\s+from\s+['\"]@/api/generated['\"]",
                re.MULTILINE,
            )
            if pattern.search(text):
                files.append(path.relative_to(WEB_ROOT).as_posix())
                break

    for root_name in ("src", "shared", "server"):
        root = WEB_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.d.ts"):
            files.append(path.relative_to(WEB_ROOT).as_posix())

    deduped = list(dict.fromkeys(files))
    deduped.sort()
    return deduped


def _run_targeted_typecheck(specs: tuple[str, ...]) -> None:
    files = _collect_targeted_typecheck_files(specs)
    if not files:
        print("No frontend consumers import the touched generated layers; skipping targeted typecheck.")
        return

    _print_header("Frontend Typecheck (Touched APIs)")
    config = {
        "extends": "./tsconfig.json",
        "files": files,
    }
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="tsconfig.contract-fast.",
        dir=WEB_ROOT,
        delete=False,
    ) as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
        temp_name = Path(handle.name)

    try:
        _run(["pnpm", "exec", "tsc", "-p", temp_name.name, "--noEmit", "--pretty", "false"], cwd=WEB_ROOT)
    finally:
        temp_name.unlink(missing_ok=True)


def _run_full_typecheck() -> None:
    _print_header("Frontend Typecheck (Full)")
    _run(["pnpm", "exec", "tsc", "-p", "tsconfig.json", "--noEmit", "--pretty", "false"], cwd=WEB_ROOT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the contract freshness and compatibility gate.")
    parser.add_argument("--mode", choices=("fast", "full"), default="full")
    parser.add_argument(
        "--base-ref",
        default=os.getenv("GITHUB_BASE_REF", "origin/main"),
        help="Base ref used to detect touched routes in fast mode.",
    )
    parser.add_argument(
        "--refresh-only",
        action="store_true",
        help="Regenerate OpenAPI and generated type artifacts but skip diff and typecheck steps.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode = args.mode
    selected_specs = ALL_SPECS
    changed_files: list[str] = []

    if mode == "fast":
        changed_files = _git_changed_files(args.base_ref)
        selected_specs = _detect_touched_specs(changed_files)
        if selected_specs == ALL_SPECS:
            print("Fast mode widened to full artifact coverage.")
        else:
            print("Fast mode selected specs:")
            for spec_name in selected_specs:
                print(f"  - {spec_name}")

    _regenerate_openapi(selected_specs)
    _regenerate_types(selected_specs)

    if args.refresh_only:
        print("\nRefresh completed.")
        return

    diff_paths = _selected_diff_paths(selected_specs)
    _print_header("Check Generated Drift")
    _check_diff(
        diff_paths,
        failure_heading="Contract artifact freshness",
        failure_help=[
            "Run the required regeneration sequence and commit the results:",
            "  pnpm run generate:contracts",
        ],
    )

    if mode == "fast":
        _run_targeted_typecheck(selected_specs)
    else:
        _run_full_typecheck()

    print("\nContract compliance gate passed.")


if __name__ == "__main__":
    main()
