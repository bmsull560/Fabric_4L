"""Bulk-add __future__ annotations and modernize typing constructs for Layer 4."""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOTS = [
    Path(r"c:\Users\BBB\Fabric_4L\services\layer4-agents\src"),
    Path(r"c:\Users\BBB\Fabric_4L\services\layer4-agents\tests"),
    Path(r"c:\Users\BBB\Fabric_4L\value_fabric\layer4"),
]

SKIP_DIRS = {".venv", ".tmp", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", ".hypothesis"}

FUTURE_IMPORT = "from __future__ import annotations"

LEGACY_TYPES = {
    "Optional": lambda inner: f"{inner} | None",
    "List": lambda inner: f"list[{inner}]",
    "Dict": lambda inner: f"dict[{inner}]",
    "Tuple": lambda inner: f"tuple[{inner}]",
    "Set": lambda inner: f"set[{inner}]",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_matching_bracket(text: str, start: int) -> int:
    """Find index of the matching `]` for `[` at *start*."""
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
        i += 1
    return i - 1 if depth == 0 else -1


def _split_union_args(text: str) -> list[str]:
    """Split comma-separated top-level arguments inside Union[...]."""
    args: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in text:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        args.append("".join(current).strip())
    return args


def _replace_outside_strings(text: str, pattern: re.Pattern, repl) -> str:
    """Replace regex matches only outside quoted strings and comments."""
    result: list[str] = []
    i = 0
    while i < len(text):
        # String literal
        if text[i] in ('"', "'"):
            quote = text[i]
            j = i + 1
            while j < len(text):
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == quote:
                    break
                j += 1
            j = min(j + 1, len(text))
            result.append(text[i:j])
            i = j
            continue
        # Comment
        if text[i] == "#":
            j = text.find("\n", i)
            if j == -1:
                j = len(text)
            result.append(text[i:j])
            i = j
            continue
        # Try match
        m = pattern.match(text, i)
        if m:
            result.append(repl(m))
            i = m.end()
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _modernize_legacy_types(text: str) -> str:
    """Replace Optional, List, Dict, Tuple, Set with modern equivalents."""

    def _union_repl(m: re.Match) -> str:
        inner = m.group(1)
        args = _split_union_args(inner)
        return " | ".join(args)

    # Union first (so Union[Optional[int], str] doesn't double-process)
    text = _replace_outside_strings(
        text,
        re.compile(r"\bUnion\["),
        lambda m: f"{_split_union_args(text[m.end():_find_matching_bracket(text, m.end()-1)])}".replace("', '", " | ").replace("['", "").replace("']", ""),
    )

    # Re-do Union with a cleaner approach
    def replace_unions(src: str) -> str:
        out: list[str] = []
        i = 0
        while i < len(src):
            if src[i] in ('"', "'"):
                quote = src[i]
                j = i + 1
                while j < len(src):
                    if src[j] == "\\":
                        j += 2
                        continue
                    if src[j] == quote:
                        break
                    j += 1
                j = min(j + 1, len(src))
                out.append(src[i:j])
                i = j
                continue
            if src[i] == "#":
                j = src.find("\n", i)
                if j == -1:
                    j = len(src)
                out.append(src[i:j])
                i = j
                continue
            if src.startswith("Union[", i):
                end = _find_matching_bracket(src, i + 5)
                if end > i:
                    inner = src[i + 6:end]
                    args = _split_union_args(inner)
                    out.append(" | ".join(args))
                    i = end + 1
                    continue
            out.append(src[i])
            i += 1
        return "".join(out)

    text = replace_unions(text)

    def replace_others(src: str, name: str, formatter) -> str:
        out: list[str] = []
        i = 0
        while i < len(src):
            if src[i] in ('"', "'"):
                quote = src[i]
                j = i + 1
                while j < len(src):
                    if src[j] == "\\":
                        j += 2
                        continue
                    if src[j] == quote:
                        break
                    j += 1
                j = min(j + 1, len(src))
                out.append(src[i:j])
                i = j
                continue
            if src[i] == "#":
                j = src.find("\n", i)
                if j == -1:
                    j = len(src)
                out.append(src[i:j])
                i = j
                continue
            if src.startswith(name + "[", i):
                end = _find_matching_bracket(src, i + len(name))
                if end > i:
                    inner = src[i + len(name) + 1:end]
                    out.append(formatter(inner))
                    i = end + 1
                    continue
            out.append(src[i])
            i += 1
        return "".join(out)

    for name, formatter in LEGACY_TYPES.items():
        text = replace_others(text, name, formatter)

    return text


def _add_future_import(text: str) -> str:
    """Insert `from __future__ import annotations` if missing."""
    if FUTURE_IMPORT in text:
        return text
    lines = text.splitlines(keepends=True)
    # Find insertion point: after module docstring, or at top
    insert_idx = 0
    if lines and lines[0].startswith('"""'):
        # Single-line docstring
        if lines[0].rstrip().endswith('"""') and lines[0].count('"""') == 2:
            insert_idx = 1
        else:
            # Multi-line docstring
            for idx, line in enumerate(lines[1:], start=1):
                if '"""' in line:
                    insert_idx = idx + 1
                    break
    # Skip blank lines after docstring
    while insert_idx < len(lines) and lines[insert_idx].strip() == "":
        insert_idx += 1
    lines.insert(insert_idx, FUTURE_IMPORT + "\n")
    # Ensure blank line after
    if insert_idx + 1 < len(lines) and lines[insert_idx + 1].strip() != "":
        lines.insert(insert_idx + 1, "\n")
    return "".join(lines)


def _cleanup_typing_imports(text: str) -> str:
    """Remove unused legacy typing imports after modernization."""
    # Find `from typing import ...` lines
    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from typing import "):
            names_str = stripped[len("from typing import "):]
            # Handle parentheses multi-line style
            if "(" in names_str:
                new_lines.append(line)
                continue
            names = [n.strip() for n in names_str.split(",")]
            # Remove legacy types that are no longer referenced
            remaining = [n for n in names if n not in LEGACY_TYPES or n in text]
            # But we need to check if the legacy name still appears in the text
            remaining = [n for n in names if n not in LEGACY_TYPES or re.search(rf"\b{n}\[", text)]
            if not remaining:
                continue  # Drop whole line
            if len(remaining) == 1:
                new_lines.append(f"from typing import {remaining[0]}\n")
            else:
                new_lines.append(f"from typing import {', '.join(remaining)}\n")
            continue
        new_lines.append(line)
    return "".join(new_lines)


def _process_file(path: Path) -> tuple[bool, list[str]]:
    """Process a single file. Returns (changed, log_messages)."""
    try:
        original = path.read_text(encoding="utf-8")
    except Exception as exc:
        return False, [f"  READ ERROR: {exc}"]

    text = original
    logs: list[str] = []
    changed = False

    # Step 1: add future import
    if FUTURE_IMPORT not in text:
        text = _add_future_import(text)
        logs.append("  + added __future__ annotations")
        changed = True

    # Step 2: modernize legacy types
    modernized = _modernize_legacy_types(text)
    if modernized != text:
        logs.append("  + modernized legacy typing")
        text = modernized
        changed = True

    # Step 3: cleanup typing imports
    cleaned = _cleanup_typing_imports(text)
    if cleaned != text:
        logs.append("  + cleaned typing imports")
        text = cleaned
        changed = True

    if changed:
        try:
            path.write_text(text, encoding="utf-8")
        except Exception as exc:
            return False, [f"  WRITE ERROR: {exc}"]

    return changed, logs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    all_files: list[Path] = []
    for root in ROOTS:
        if not root.exists():
            continue
        for r, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f.endswith(".py"):
                    all_files.append(Path(r) / f)

    changed_count = 0
    unchanged_count = 0
    error_count = 0

    for path in sorted(all_files):
        rel = path.relative_to(Path(r"c:\Users\BBB\Fabric_4L"))
        changed, logs = _process_file(path)
        if changed:
            changed_count += 1
            print(f"MODIFIED {rel}")
            for log in logs:
                print(log)
        elif logs and any("ERROR" in l for l in logs):
            error_count += 1
            print(f"ERROR {rel}")
            for log in logs:
                print(log)
        else:
            unchanged_count += 1

    print(f"\n--- Summary ---")
    print(f"Total scanned: {len(all_files)}")
    print(f"Modified:      {changed_count}")
    print(f"Unchanged:     {unchanged_count}")
    print(f"Errors:        {error_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
