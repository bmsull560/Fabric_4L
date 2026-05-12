#!/usr/bin/env python3
"""Fail CI when Neo4j app clients map NEO4J_PASSWORD from auth-style secret keys."""
from __future__ import annotations

from pathlib import Path
import sys
import yaml

ALLOWED_PASSWORD_KEYS = {"neo4j_password", "NEO4J_PASSWORD", "password", "NEO4J_APP_PASSWORD"}
FORBIDDEN_PASSWORD_KEYS = {"auth", "NEO4J_AUTH"}
SKIP_DIR_PARTS = {"routing", "chaos", "vault", "infisical", "monitoring", "gitops"}


def iter_yaml_files(root: Path):
    for path in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        if any(part in SKIP_DIR_PARTS for part in path.parts):
            continue
        yield path


def as_docs(path: Path):
    try:
        return [d for d in yaml.safe_load_all(path.read_text(encoding="utf-8")) if isinstance(d, dict)]
    except Exception as exc:
        print(f"WARN: could not parse {path}: {exc}", file=sys.stderr)
        return []


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    k8s_root = repo_root / "k8s"
    violations = []

    for yf in iter_yaml_files(k8s_root):
        for doc in as_docs(yf):
            kind = doc.get("kind")
            if kind not in {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob", "Pod"}:
                continue
            tpl = (((doc.get("spec") or {}).get("template") or {}).get("spec") or {})
            containers = tpl.get("containers") or []
            for c in containers:
                cname = c.get("name", "<container>")
                for env in c.get("env") or []:
                    if env.get("name") != "NEO4J_PASSWORD":
                        continue
                    ref = ((env.get("valueFrom") or {}).get("secretKeyRef") or {})
                    key = ref.get("key")
                    if not key:
                        continue
                    if key in FORBIDDEN_PASSWORD_KEYS:
                        violations.append(f"{yf}: container={cname} maps NEO4J_PASSWORD from forbidden key '{key}'")
                    elif key not in ALLOWED_PASSWORD_KEYS:
                        violations.append(f"{yf}: container={cname} maps NEO4J_PASSWORD from non-dedicated key '{key}'")

                for env in c.get("env") or []:
                    if env.get("name") == "NEO4J_AUTH":
                        ref = ((env.get("valueFrom") or {}).get("secretKeyRef") or {})
                        key = ref.get("key")
                        if key and key not in {"auth", "NEO4J_AUTH"}:
                            violations.append(f"{yf}: container={cname} should map NEO4J_AUTH from auth key, found '{key}'")

    if violations:
        print("FAIL: Neo4j secret key mapping violations detected:")
        for v in violations:
            print(f" - {v}")
        return 1

    print("OK: Neo4j secret key mappings are valid for app clients and Neo4j server bootstrap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
