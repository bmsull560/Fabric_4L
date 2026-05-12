#!/usr/bin/env python3
"""Static route auth inventory for layer runtime and service routers.

By default this script reports unauthenticated routes that are either system
endpoints or explicitly listed in ``contracts/route-auth-allowlist.yaml``. It
does not replace the existing failing auth dependency gate unless called with
``--enforce``.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
AUTH_SIGNAL_NAMES = {
    "Security",
    "require_authenticated",
    "require_auth",
    "require_role",
    "require_permission",
    "get_request_context",
    "get_verified_tenant_id",
    "get_current_api_key",
}
AUTH_HINT_TOKENS = (
    "auth",
    "tenant",
    "context",
    "api_key",
    "token",
    "current_user",
    "principal",
)
DEFAULT_SCAN_GLOBS = [
    "value_fabric/layer*/api/routes/*.py",
    "services/layer*/src/api/routes/*.py",
    "services/layer*/src/*/api/routes/*.py",
]
SYSTEM_ROUTE_PATTERNS = ("/", "/health", "/healthz", "/ready", "/metrics", "/docs", "/redoc", "/openapi")


@dataclass
class RouteRecord:
    method: str
    path: str
    source: str
    function: str
    auth_present: bool
    allowlisted: bool = False
    system_endpoint: bool = False


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return call_name(node.func)
    return None


def literal_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def has_auth_dependency(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        callee = call_name(sub.func) or ""
        if callee in AUTH_SIGNAL_NAMES:
            return True
        if callee in {"Depends", "Security"} and sub.args:
            dep_name = (call_name(sub.args[0]) or "").lower()
            if dep_name and any(token in dep_name for token in AUTH_HINT_TOKENS):
                return True
    return False


def extract_router_auth_defaults(tree: ast.Module) -> dict[str, bool]:
    defaults: dict[str, bool] = {}
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        name = node.targets[0].id
        value = node.value
        if isinstance(value, ast.Call) and call_name(value.func) == "APIRouter":
            defaults[name] = has_auth_dependency(value)
    return defaults


def extract_routes(py_file: Path, repo_root: Path) -> list[RouteRecord]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    router_defaults = extract_router_auth_defaults(tree)
    source = py_file.relative_to(repo_root).as_posix()
    routes: list[RouteRecord] = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        fn_auth = has_auth_dependency(node)
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                continue
            method = deco.func.attr.lower()
            if method not in HTTP_METHODS:
                continue
            router_name = call_name(deco.func.value) or ""
            route_path = literal_str(deco.args[0]) if deco.args else "/"
            route_path = route_path or "/"
            auth = fn_auth or has_auth_dependency(deco) or router_defaults.get(router_name, False)
            routes.append(
                RouteRecord(
                    method=method.upper(),
                    path=route_path,
                    source=source,
                    function=node.name,
                    auth_present=auth,
                )
            )
    return routes


def load_allowlist(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("allowlist", [])


def is_allowlisted(route: RouteRecord, allowlist: list[dict[str, Any]]) -> bool:
    for item in allowlist:
        method = str(item.get("method", "*")).upper()
        pattern = str(item.get("path", ""))
        if method not in {"*", route.method}:
            continue
        if fnmatch.fnmatch(route.path, pattern):
            return True
    return False


def is_system_endpoint(path: str) -> bool:
    return any(path == pattern or path.startswith(f"{pattern}/") for pattern in SYSTEM_ROUTE_PATTERNS)


def discover_router_files(repo_root: Path, globs: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in globs:
        files.extend(repo_root.glob(pattern))
    return sorted({p for p in files if p.is_file() and not p.name.startswith("_")})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allowlist", default="contracts/route-auth-allowlist.yaml")
    parser.add_argument("--inventory-json", default="")
    parser.add_argument("--enforce", action="store_true", help="Fail on non-system, non-allowlisted unauthenticated routes")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    allowlist = load_allowlist(repo_root / args.allowlist)
    router_files = discover_router_files(repo_root, DEFAULT_SCAN_GLOBS)

    all_routes: list[RouteRecord] = []
    for file in router_files:
        all_routes.extend(extract_routes(file, repo_root))

    unauth_inventory: list[RouteRecord] = []
    failures: list[RouteRecord] = []

    for route in all_routes:
        if route.auth_present:
            continue
        route.allowlisted = is_allowlisted(route, allowlist)
        route.system_endpoint = is_system_endpoint(route.path)
        if route.allowlisted or route.system_endpoint:
            unauth_inventory.append(route)
            continue
        failures.append(route)

    if args.inventory_json:
        payload = [asdict(r) for r in sorted(unauth_inventory, key=lambda r: (r.method, r.path, r.source, r.function))]
        Path(args.inventory_json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Scanned router files: {len(router_files)}")
    print(f"Scanned routes: {len(all_routes)}")
    print(f"Unauthenticated inventory (system/allowlisted): {len(unauth_inventory)}")
    print(f"Unauthenticated routes requiring review: {len(failures)}")

    if failures:
        print("\nUnauthenticated routes not in contracts/route-auth-allowlist.yaml:")
        for route in failures:
            print(f"- {route.method} {route.path} [{route.source}:{route.function}]")
        if args.enforce:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
