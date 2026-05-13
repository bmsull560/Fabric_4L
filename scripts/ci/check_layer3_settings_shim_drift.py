#!/usr/bin/env python3
"""Validate Layer 3 settings shim drift and operational field coverage."""

from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "value_fabric/layer3/config/settings.py"
SHIM = ROOT / "value_fabric/layer3/config.py"

REQUIRED_FIELDS = {
    "API_PORT",
    "NEO4J_URI",
    "NEO4J_USER",
    "NEO4J_PASSWORD",
    "NEO4J_DATABASE",
    "RATE_LIMIT_ENABLED",
    "RATE_LIMIT_REQUESTS_PER_MINUTE",
    "RATE_LIMIT_BURST_SIZE",
    "METRICS_ENABLED",
    "METRICS_PATH",
    "CORS_ORIGINS",
    "JWT_SECRET",
}


def _extract_aliases(module: ast.Module) -> set[str]:
    aliases: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and call.func.id == "Field":
                for kw in call.keywords:
                    if kw.arg == "alias" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        aliases.add(kw.value.value)
    return aliases


def _validate_shim(module: ast.Module) -> list[str]:
    errors: list[str] = []
    class_defs = [node.name for node in module.body if isinstance(node, ast.ClassDef)]
    if class_defs:
        errors.append(f"Shim must not define classes, found: {', '.join(class_defs)}")

    fn_defs = [node.name for node in module.body if isinstance(node, ast.FunctionDef)]
    if fn_defs:
        errors.append(f"Shim must not define functions, found: {', '.join(fn_defs)}")

    import_ok = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "value_fabric.layer3.config.settings"
        and {alias.name for alias in node.names} == {"Settings", "get_settings"}
        for node in module.body
    )
    if not import_ok:
        errors.append("Shim must re-export Settings and get_settings from value_fabric.layer3.config.settings")
    return errors


def main() -> int:
    canonical_ast = ast.parse(CANONICAL.read_text(encoding="utf-8"))
    shim_ast = ast.parse(SHIM.read_text(encoding="utf-8"))

    errors = _validate_shim(shim_ast)

    aliases = _extract_aliases(canonical_ast)
    missing = sorted(REQUIRED_FIELDS - aliases)
    if missing:
        errors.append(f"Canonical settings is missing required operational aliases: {', '.join(missing)}")

    if errors:
        print("Layer 3 settings shim drift detected:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Layer 3 settings shim drift check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
