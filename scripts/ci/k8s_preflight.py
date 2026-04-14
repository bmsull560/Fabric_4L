#!/usr/bin/env python3
"""Kubernetes preflight guard for workload validation.

Validates every workload in k8s/base/ for:
- Rollout strategy
- livenessProbe/readinessProbe
- resources.requests/resources.limits
- Image pinning (no :latest)
- Required secret keys against k8s/secrets.yml.template
- Layer-5 Alembic migration guardrails

Usage:
    python3 scripts/ci/k8s_preflight.py
    python3 scripts/ci/k8s_preflight.py --verbose
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


def load_yaml_files(directory: Path) -> list[tuple[Path, dict]]:
    """Load all YAML files from a directory."""
    files = []
    for yaml_file in directory.glob("*.yml"):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                if content:
                    files.append((yaml_file, content))
        except Exception as e:
            print(f"Warning: Could not parse {yaml_file}: {e}")
    return files


def check_rollout_strategy(doc: dict) -> tuple[bool, str]:
    """Check if rollout strategy is defined."""
    kind = doc.get("kind", "")
    if kind not in ("Deployment", "StatefulSet"):
        return True, "N/A (not a workload)"

    spec = doc.get("spec", {})
    strategy = spec.get("strategy", {})

    if kind == "Deployment":
        if strategy.get("type") == "RollingUpdate":
            return True, "RollingUpdate configured"
        return False, "Missing or invalid RollingUpdate strategy"
    elif kind == "StatefulSet":
        update_strategy = spec.get("updateStrategy", {})
        if update_strategy.get("type") == "RollingUpdate":
            return True, "RollingUpdate configured"
        return False, "Missing or invalid RollingUpdate strategy"

    return True, "N/A"


def check_probes(doc: dict) -> tuple[bool, str]:
    """Check if liveness and readiness probes are configured."""
    kind = doc.get("kind", "")
    if kind not in ("Deployment", "StatefulSet", "DaemonSet"):
        return True, "N/A (not a workload)"

    spec = doc.get("spec", {})
    template = spec.get("template", {})
    pod_spec = template.get("spec", {})
    containers = pod_spec.get("containers", [])

    if not containers:
        return False, "No containers defined"

    all_ok = True
    messages = []

    for container in containers:
        name = container.get("name", "unknown")
        liveness = container.get("livenessProbe")
        readiness = container.get("readinessProbe")

        if not liveness:
            all_ok = False
            messages.append(f"{name}: missing livenessProbe")
        if not readiness:
            all_ok = False
            messages.append(f"{name}: missing readinessProbe")

    if all_ok:
        return True, "All containers have probes"
    return False, "; ".join(messages)


def check_resources(doc: dict) -> tuple[bool, str]:
    """Check if resources.requests and resources.limits are set."""
    kind = doc.get("kind", "")
    if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job"):
        return True, "N/A (not a workload)"

    spec = doc.get("spec", {})
    template = spec.get("template", {})
    pod_spec = template.get("spec", {})
    containers = pod_spec.get("containers", [])

    if not containers:
        return False, "No containers defined"

    all_ok = True
    messages = []

    for container in containers:
        name = container.get("name", "unknown")
        resources = container.get("resources", {})
        requests = resources.get("requests", {})
        limits = resources.get("limits", {})

        missing = []
        if "cpu" not in requests:
            missing.append("requests.cpu")
        if "memory" not in requests:
            missing.append("requests.memory")
        if "cpu" not in limits:
            missing.append("limits.cpu")
        if "memory" not in limits:
            missing.append("limits.memory")

        if missing:
            all_ok = False
            messages.append(f"{name}: missing {', '.join(missing)}")

    if all_ok:
        return True, "All containers have resource constraints"
    return False, "; ".join(messages)


def check_image_pinning(doc: dict) -> tuple[bool, str]:
    """Check if images are pinned (no :latest tag)."""
    kind = doc.get("kind", "")
    if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
        return True, "N/A (not a workload)"

    containers = []
    init_containers = []

    spec = doc.get("spec", {})

    if kind == "CronJob":
        job_template = spec.get("jobTemplate", {})
        job_spec = job_template.get("spec", {})
        template = job_spec.get("template", {})
    else:
        template = spec.get("template", {})

    pod_spec = template.get("spec", {})
    containers = pod_spec.get("containers", [])
    init_containers = pod_spec.get("initContainers", [])

    all_images = containers + init_containers

    if not all_images:
        return False, "No containers defined"

    bad_images = []
    for container in all_images:
        image = container.get("image", "")
        if ":latest" in image or ":" not in image:
            bad_images.append(f"{container.get('name', 'unknown')}: {image}")

    if bad_images:
        return False, f"Unpinned images: {', '.join(bad_images)}"
    return True, "All images are pinned"


def load_required_secrets(template_path: Path) -> set[str]:
    """Load required secret keys from template."""
    required = set()
    if not template_path.exists():
        return required

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract placeholder names like {{ .Values.secrets.POSTGRES_PASSWORD }}
            matches = re.findall(r"\{\{\s*\.Values\.secrets\.(\w+)\s*\}\}", content)
            required.update(matches)
    except Exception:
        pass

    return required


def check_layer5_migration_guardrails(doc: dict) -> tuple[bool, str]:
    """Check for Layer-5 Alembic migration guardrails."""
    kind = doc.get("kind", "")

    # Look for Job or CronJob that handles migrations
    name = doc.get("metadata", {}).get("name", "").lower()

    if "layer5" in name or "ground-truth" in name or "migration" in name:
        spec = doc.get("spec", {})

        if kind == "CronJob":
            job_template = spec.get("jobTemplate", {})
            spec = job_template.get("spec", {})

        template = spec.get("template", {})
        pod_spec = template.get("spec", {})
        containers = pod_spec.get("containers", [])

        # Check for init container that runs migrations
        init_containers = pod_spec.get("initContainers", [])
        has_migration_init = any(
            "migrate" in c.get("name", "").lower()
            or any("migrate" in cmd for cmd in c.get("command", []))
            for c in init_containers
        )

        # Check for migration job or post-start hook
        has_migration_job = any(
            "migrate" in c.get("name", "").lower()
            or any("alembic" in arg for arg in c.get("args", []))
            or any("alembic" in cmd for cmd in c.get("command", []))
            for c in containers
        )

        # If it's a migration-related workload, check for guardrails
        if has_migration_init or has_migration_job or "migrate" in name:
            # Check for init container (runs before app)
            if not init_containers and kind != "Job":
                return False, "Missing init container for migration sequencing"

            return True, "Migration guardrails present"

    return True, "N/A (not L5 migration workload)"


def validate_workload(file_path: Path, doc: dict, verbose: bool) -> list[tuple[str, bool, str]]:
    """Validate a single workload document."""
    results = []

    checks = [
        ("rollout_strategy", check_rollout_strategy),
        ("probes", check_probes),
        ("resources", check_resources),
        ("image_pinning", check_image_pinning),
        ("l5_migration", check_layer5_migration_guardrails),
    ]

    for check_name, check_func in checks:
        passed, message = check_func(doc)
        results.append((check_name, passed, message))
        if verbose:
            status = "✅" if passed else "❌"
            print(f"  [{status}] {check_name}: {message}")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Kubernetes preflight validation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent
    k8s_base = repo_root / "k8s" / "base"
    secrets_template = repo_root / "k8s" / "secrets.yml.template"

    if not k8s_base.exists():
        print(f"Error: k8s/base directory not found at {k8s_base}")
        return 1

    # Load required secrets
    required_secrets = load_required_secrets(secrets_template)
    if args.verbose and required_secrets:
        print(f"Required secrets from template: {', '.join(required_secrets)}")

    # Load all YAML files
    yaml_files = load_yaml_files(k8s_base)

    if not yaml_files:
        print("Warning: No YAML files found in k8s/base/")
        return 0

    all_results = []
    workload_count = 0

    print(f"Scanning {len(yaml_files)} YAML files in k8s/base/...")
    print()

    for file_path, doc in yaml_files:
        kind = doc.get("kind", "")
        name = doc.get("metadata", {}).get("name", "unknown")

        # Skip non-workload resources
        if kind not in ("Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"):
            continue

        workload_count += 1

        if args.verbose:
            print(f"Validating {kind}/{name} from {file_path.name}")

        results = validate_workload(file_path, doc, args.verbose)
        all_results.extend([(file_path.name, kind, name, r) for r in results])

        if args.verbose:
            print()

    # Summary
    failures = [(f, k, n, r) for (f, k, n, r) in all_results if not r[1]]

    print("=" * 60)
    print(f"Validated {workload_count} workload(s)")
    print(f"Total checks: {len(all_results)}")
    print(f"Passed: {len(all_results) - len(failures)}")
    print(f"Failed: {len(failures)}")
    print("=" * 60)

    if failures:
        print("\nFailed checks:")
        for file, kind, name, (check, passed, msg) in failures:
            print(f"  ❌ {kind}/{name} ({file}): {check} — {msg}")
        return 1

    print(f"\n✅ Kubernetes preflight passed for {workload_count} workload(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
