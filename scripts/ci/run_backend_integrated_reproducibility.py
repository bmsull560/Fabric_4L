#!/usr/bin/env python3
"""Run and verify backend-integrated J1/J11 reproducibility evidence.

This runner is intentionally narrow. It exercises the local/CI Docker-backed
backend-integrated path documented in
``docs/validation/backend_integrated/backend_integrated_reproducibility_handoff.md``
and verifies retained seed and Playwright artifacts without making launch claims.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = REPO_ROOT / "apps" / "web"
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "artifacts" / "live-workflow-validation"
DEFAULT_COMPOSE_FILES = [
    REPO_ROOT / "docker-compose.live.yml",
    REPO_ROOT / ".tmp" / "docker-compose.j11.override.yml",
]
REQUIRED_SERVICES = ["postgres", "redis", "neo4j", "minio", "layer1", "layer4", "frontend"]
SECRET_KEY_PATTERN = re.compile(r"(SECRET|TOKEN|PASSWORD|PASSWD|KEY|AUTH)", re.IGNORECASE)
SECRET_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("url credentials", re.compile(r"(?i)(postgresql|postgres|mysql|redis|mongodb)://[^\s@]+:[^\s@]+@")),
    ("authorization header", re.compile(r"(?i)(Authorization\s*[:=]\s*)\S+")),
    (
        "secret assignment",
        re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)\s*[=:]\s*\S+"),
    ),
)


class PhaseError(RuntimeError):
    """Raised when a reproducibility phase fails."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_text(text: str) -> str:
    redacted = text
    for _label, pattern in SECRET_VALUE_PATTERNS:
        redacted = pattern.sub(lambda match: match.group(1) + "[REDACTED]" if match.groups() else "[REDACTED]", redacted)
    return redacted


def rel_env_path(path: Path, *, base: Path) -> str:
    return Path(os.path.relpath(path, base)).as_posix()


def is_windows() -> bool:
    return platform.system().lower().startswith("win")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PhaseError(f"required JSON artifact is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PhaseError(f"invalid JSON artifact {path}: {exc}") from exc


def parse_junit(path: Path) -> dict[str, int]:
    try:
        root = ElementTree.parse(path).getroot()
    except FileNotFoundError as exc:
        raise PhaseError(f"required JUnit artifact is missing: {path}") from exc
    except ElementTree.ParseError as exc:
        raise PhaseError(f"invalid JUnit XML {path}: {exc}") from exc

    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}

    def add_counts(node: ElementTree.Element) -> None:
        for key in totals:
            value = node.attrib.get(key)
            if value is not None:
                totals[key] += int(float(value))

    if root.tag == "testsuite":
        add_counts(root)
    elif root.tag == "testsuites":
        if any(key in root.attrib for key in totals):
            add_counts(root)
        else:
            for suite in root.findall("testsuite"):
                add_counts(suite)
    else:
        raise PhaseError(f"unsupported JUnit root element in {path}: {root.tag}")

    return totals


def resolve_release_candidate_sha(explicit: str | None) -> str:
    for candidate in (explicit, os.environ.get("RELEASE_CANDIDATE_SHA"), os.environ.get("GITHUB_SHA")):
        if candidate and candidate.strip():
            return candidate.strip()

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    raise PhaseError(
        "release-candidate SHA is required; pass --release-candidate-sha or set RELEASE_CANDIDATE_SHA/GITHUB_SHA"
    )


def base_env(args: argparse.Namespace, artifact_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PLAYWRIGHT_BACKEND_URL": args.backend_url,
            "PLAYWRIGHT_LIVE_MODE": "true",
            "PLAYWRIGHT_LIVE_FRONTEND_URL": args.frontend_url,
            "PLAYWRIGHT_BASE_URL": args.frontend_url,
            "VITE_USE_MOCKS": "false",
            "VITE_ENABLE_MOCK_FALLBACK": "false",
            "E2E_SEED_DATA": "false",
            "SEED_REPORT_JSON": str(artifact_dir / "seed-report.json"),
        }
    )
    env.pop("MSW", None)
    env.pop("MOCKS_ENABLED", None)
    return env


def printable_env_delta(env: dict[str, str]) -> dict[str, str]:
    keys = [
        "PLAYWRIGHT_BACKEND_URL",
        "PLAYWRIGHT_LIVE_MODE",
        "PLAYWRIGHT_LIVE_FRONTEND_URL",
        "PLAYWRIGHT_BASE_URL",
        "VITE_USE_MOCKS",
        "VITE_ENABLE_MOCK_FALLBACK",
        "E2E_SEED_DATA",
        "SEED_REPORT_JSON",
        "SERVICE_AUTH_SECRET",
        "JWT_SECRET",
    ]
    visible: dict[str, str] = {}
    for key in keys:
        if key not in env:
            continue
        visible[key] = "[REDACTED]" if SECRET_KEY_PATTERN.search(key) else env[key]
    visible["MSW"] = "<unset>"
    visible["MOCKS_ENABLED"] = "<unset>"
    return visible


def run_phase(
    *,
    name: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    phases: list[dict[str, Any]],
) -> None:
    print(f"\n## {name}")
    print("$ " + " ".join(command))
    started = now_iso()
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = redact_text(result.stdout or "")
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    phases.append(
        {
            "name": name,
            "command": command,
            "cwd": str(cwd),
            "startedAt": started,
            "finishedAt": now_iso(),
            "returnCode": result.returncode,
        }
    )
    if result.returncode != 0:
        raise PhaseError(f"{name} failed with exit code {result.returncode}")


def docker_command(compose_files: list[Path]) -> list[str]:
    command = ["docker", "compose"]
    for compose_file in compose_files:
        command.extend(["-f", str(compose_file)])
    command.extend(["up", "-d", "--build", "--wait", *REQUIRED_SERVICES])
    return command


def seed_command() -> tuple[list[str], Path]:
    if is_windows():
        return (
            [
                "cmd",
                "/c",
                r"apps\web\node_modules\.bin\tsx.cmd",
                r"scripts\db\seed-e2e-data.ts",
                "--base-url=http://127.0.0.1:8004",
            ],
            REPO_ROOT,
        )
    return (
        [
            "pnpm",
            "--dir",
            "apps/web",
            "exec",
            "tsx",
            "../../scripts/db/seed-e2e-data.ts",
            "--base-url=http://127.0.0.1:8004",
        ],
        REPO_ROOT,
    )


def playwright_command(specs: list[str]) -> tuple[list[str], Path]:
    if is_windows():
        return (
            ["cmd", "/c", r"node_modules\.bin\playwright.cmd", "test", "--project=backend-integrated", *specs],
            WEB_DIR,
        )
    return (
        ["pnpm", "exec", "playwright", "test", "--project=backend-integrated", *specs],
        WEB_DIR,
    )


def guard_command(mode: str) -> tuple[list[str], Path]:
    return (["node", "apps/web/scripts/live-env-guard.mjs", mode], REPO_ROOT)


def verify_seed(seed_path: Path) -> dict[str, Any]:
    seed = load_json(seed_path)
    aggregate_status = seed.get("aggregateStatus", seed.get("status"))
    required_rows_present = seed.get("requiredRowsPresent")
    if aggregate_status != "present":
        raise PhaseError(f"seed report aggregateStatus/status must be present, got {aggregate_status!r}")
    if required_rows_present is not True:
        raise PhaseError(f"seed report requiredRowsPresent must be true, got {required_rows_present!r}")
    return {"path": str(seed_path), "aggregateStatus": aggregate_status, "requiredRowsPresent": required_rows_present}


def verify_junit(path: Path, *, expected_tests: int | None = None) -> dict[str, Any]:
    counts = parse_junit(path)
    if counts["failures"] != 0 or counts["errors"] != 0:
        raise PhaseError(f"{path} must have failures=0 and errors=0, got {counts}")
    if expected_tests is not None and counts["tests"] != expected_tests:
        raise PhaseError(f"{path} must have tests={expected_tests}, got {counts['tests']}")
    return {"path": str(path), **counts}


def write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run backend-integrated J1/J11 reproducibility evidence")
    parser.add_argument("--release-candidate-sha", help="Release-candidate commit SHA to record in evidence")
    parser.add_argument("--artifact-dir", default=str(DEFAULT_ARTIFACT_DIR), help="Artifact root")
    parser.add_argument("--frontend-url", default="http://localhost:3001", help="Frontend URL for Playwright")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8004", help="Layer 4 backend URL for seeding")
    parser.add_argument(
        "--compose-file",
        action="append",
        dest="compose_files",
        help="Docker compose file. Can be provided multiple times.",
    )
    parser.add_argument("--skip-stack-start", action="store_true", help="Use an already-running approved stack")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    artifact_dir = Path(args.artifact_dir)
    if not artifact_dir.is_absolute():
        artifact_dir = REPO_ROOT / artifact_dir
    artifact_dir = artifact_dir.resolve()
    playwright_dir = artifact_dir / "playwright"
    summary_path = artifact_dir / "backend-integrated-reproducibility-summary.json"
    compose_files = [Path(p).resolve() for p in args.compose_files] if args.compose_files else DEFAULT_COMPOSE_FILES
    phases: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "generatedAt": now_iso(),
        "status": "FAIL",
        "releaseCandidateSha": None,
        "artifactDir": str(artifact_dir),
        "frontendUrl": args.frontend_url,
        "backendUrl": args.backend_url,
        "composeFiles": [str(path) for path in compose_files],
        "requiredServices": REQUIRED_SERVICES,
        "skipStackStart": args.skip_stack_start,
        "environment": {},
        "phases": phases,
        "artifacts": {},
    }

    try:
        release_sha = resolve_release_candidate_sha(args.release_candidate_sha)
        env = base_env(args, artifact_dir)
        summary["releaseCandidateSha"] = release_sha
        summary["environment"] = printable_env_delta(env)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        playwright_dir.mkdir(parents=True, exist_ok=True)

        if not args.skip_stack_start:
            run_phase(name="start docker-backed stack", command=docker_command(compose_files), cwd=REPO_ROOT, env=env, phases=phases)

        command, cwd = guard_command("seed")
        run_phase(name="verify seed guard", command=command, cwd=cwd, env=env, phases=phases)

        command, cwd = seed_command()
        run_phase(name="seed backend-integrated validation data", command=command, cwd=cwd, env=env, phases=phases)

        summary["artifacts"]["seedReport"] = verify_seed(artifact_dir / "seed-report.json")

        runs = [
            (
                "run J1-only backend-integrated Playwright",
                ["e2e/journeys/j1-golden-path-backend-integrated.spec.ts"],
                playwright_dir / "j1-junit.xml",
                playwright_dir / "j1-html",
                playwright_dir / "j1-test-results",
                None,
                "j1Junit",
            ),
            (
                "run J11-only backend-integrated Playwright",
                ["e2e/journeys/j11-golden-path-business-lifecycle.spec.ts"],
                playwright_dir / "j11-junit.xml",
                playwright_dir / "j11-html",
                playwright_dir / "j11-test-results",
                None,
                "j11Junit",
            ),
            (
                "run J1+J11 backend-integrated Playwright pair",
                [
                    "e2e/journeys/j1-golden-path-backend-integrated.spec.ts",
                    "e2e/journeys/j11-golden-path-business-lifecycle.spec.ts",
                ],
                playwright_dir / "junit.xml",
                playwright_dir / "html",
                playwright_dir / "test-results",
                20,
                "pairJunit",
            ),
        ]

        for name, specs, junit_path, html_path, output_path, expected_tests, artifact_key in runs:
            run_env = env.copy()
            run_env.update(
                {
                    "PLAYWRIGHT_JUNIT_FILE": rel_env_path(junit_path, base=WEB_DIR),
                    "PLAYWRIGHT_HTML_REPORT": rel_env_path(html_path, base=WEB_DIR),
                    "PLAYWRIGHT_OUTPUT_DIR": rel_env_path(output_path, base=WEB_DIR),
                }
            )
            command, cwd = guard_command("test")
            run_phase(name=f"{name} guard", command=command, cwd=cwd, env=run_env, phases=phases)
            command, cwd = playwright_command(specs)
            run_phase(name=name, command=command, cwd=cwd, env=run_env, phases=phases)
            summary["artifacts"][artifact_key] = verify_junit(junit_path, expected_tests=expected_tests)

        summary["status"] = "PASS"
        print("\n## Evidence summary")
        print(json.dumps(summary["artifacts"], indent=2, sort_keys=True))
        return 0
    except PhaseError as exc:
        summary["error"] = str(exc)
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        summary["finishedAt"] = now_iso()
        write_summary(summary_path, summary)
        print(f"\nWrote summary: {summary_path}")


if __name__ == "__main__":
    raise SystemExit(main())
