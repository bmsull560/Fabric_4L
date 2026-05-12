"""Syntax-check all Layer 4 Python files."""

from __future__ import annotations

import os
import py_compile
import sys
from pathlib import Path

ROOTS = [
    Path(r"c:\Users\BBB\Fabric_4L\services\layer4-agents\src"),
    Path(r"c:\Users\BBB\Fabric_4L\services\layer4-agents\tests"),
    Path(r"c:\Users\BBB\Fabric_4L\value_fabric\layer4"),
]
SKIP_DIRS = {".venv", ".tmp", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", ".hypothesis"}

errors: list[tuple[str, str]] = []
ok_count = 0

for root in ROOTS:
    if not root.exists():
        continue
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                path = Path(r) / f
                try:
                    py_compile.compile(str(path), doraise=True)
                    ok_count += 1
                except py_compile.PyCompileError as exc:
                    errors.append((str(path), str(exc)))

print(f"OK: {ok_count}")
if errors:
    print(f"ERRORS: {len(errors)}")
    for path, msg in errors:
        print(f"  {path}\n    {msg}")
    sys.exit(1)
else:
    print("All files syntax OK.")
    sys.exit(0)
