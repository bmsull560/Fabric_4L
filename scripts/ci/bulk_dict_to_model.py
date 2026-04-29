#!/usr/bin/env python3
"""Bulk-convert raw dict returns to TypedDictModel subclasses.

Scans Python files for ``return {`` statements and wraps each unique
function's dict returns in a generated Pydantic model.  The generated
models inherit from ``shared.models.typed_dict.TypedDictModel`` so
callers that do ``result["key"]`` continue to work.

Usage::

    python scripts/ci/bulk_dict_to_model.py <file1.py> <file2.py> ...
    python scripts/ci/bulk_dict_to_model.py --from-lint

"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Import to inject when missing
TYPED_DICT_IMPORT = "from shared.models.typed_dict import TypedDictModel\n"


def _infer_type(node: ast.AST) -> str:
    """Infer a Pydantic-friendly type string from an AST value node."""
    if isinstance(node, ast.Constant):
        val = node.value
        if val is None:
            return "Any"
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, float):
            return "float"
        if isinstance(val, str):
            return "str"
        if isinstance(val, bytes):
            return "bytes"
        return "Any"
    if isinstance(node, ast.List):
        return "list[Any]"
    if isinstance(node, ast.Tuple):
        return "tuple[Any, ...]"
    if isinstance(node, ast.Dict):
        return "dict[str, Any]"
    if isinstance(node, ast.Set):
        return "set[Any]"
    if isinstance(node, ast.Call):
        # Special-case common constructors
        func = node.func
        if isinstance(func, ast.Name):
            if func.id in ("Decimal", "uuid", "UUID"):
                return func.id
            if func.id in ("list", "set", "tuple"):
                return f"{func.id}[Any]"
            if func.id == "dict":
                return "dict[str, Any]"
        if isinstance(func, ast.Attribute):
            if func.attr in ("uuid4", "now", "today"):
                return "str"
        return "Any"
    if isinstance(node, ast.Name):
        if node.id in ("True", "False"):
            return "bool"
        if node.id == "None":
            return "Any"
        return "Any"
    if isinstance(node, ast.JoinedStr):
        return "str"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _infer_type(node.left)
        right = _infer_type(node.right)
        if left == right == "str":
            return "str"
        if left in ("int", "float") and right in ("int", "float"):
            return "float" if "float" in (left, right) else "int"
        return "Any"
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return "bool"
        return _infer_type(node.operand)
    if isinstance(node, ast.Compare):
        return "bool"
    if isinstance(node, ast.BoolOp):
        return "bool"
    if isinstance(node, ast.IfExp):
        t = _infer_type(node.body)
        f = _infer_type(node.orelse)
        if t == f:
            return t
        return "Any"
    return "Any"


def _gather_returns(tree: ast.AST, source: str) -> dict[str, list[tuple[ast.Return, ast.Dict, str]]]:
    """Group raw-dict returns by their enclosing function/method name."""
    results: dict[str, list[tuple[ast.Return, ast.Dict, str]]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            # Walk up to find enclosing function
            parent_func = None
            parent_class = None
            for ancestor in ast.walk(tree):
                # We need a more efficient parent lookup; build a map
                pass

    # More efficient: build parent map
    parent_map: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent_map[child] = node

    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, (ast.Dict, ast.DictComp, ast.Set, ast.SetComp)):
            # Skip docstring examples inside function defs (simple heuristic)
            segment = ast.get_source_segment(source, node.value)
            if segment is None:
                continue

            # Find enclosing function/class
            func_node = None
            class_node = None
            current: ast.AST = node
            while current in parent_map:
                current = parent_map[current]
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)) and func_node is None:
                    func_node = current
                if isinstance(current, ast.ClassDef) and class_node is None:
                    class_node = current
                if isinstance(current, ast.Module):
                    break

            if func_node is None:
                continue

            func_name = func_node.name
            if class_node is not None:
                func_name = f"{class_node.name}_{func_name}"

            results.setdefault(func_name, []).append((node, node.value, segment))

    return results


def _build_models(
    grouped: dict[str, list[tuple[ast.Return, ast.Dict, str]]],
) -> dict[str, tuple[str, list[tuple[int, int, int, int, str]]]]:
    """Generate model class text and replacement specs for each function group."""
    # Returns: {func_name: (model_class_text, [(start_line, start_col, end_line, end_col, replacement)])}
    out: dict[str, tuple[str, list[tuple[int, int, int, int, str]]]] = {}
    used_names: set[str] = set()

    for func_name, returns in grouped.items():
        # Collect all keys and their types across returns
        key_types: dict[str, set[str]] = {}
        key_required: dict[str, bool] = {}

        for _ret, dict_node, _segment in returns:
            present_keys: set[str] = set()
            if isinstance(dict_node, ast.Dict):
                for k, v in zip(dict_node.keys, dict_node.values):
                    if k is None:
                        # ** unpacking — skip type inference for this return
                        continue
                    key_name = None
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        key_name = k.value
                    if key_name is None:
                        continue
                    present_keys.add(key_name)
                    t = _infer_type(v)
                    key_types.setdefault(key_name, set()).add(t)

                for key_name in key_types:
                    key_required[key_name] = key_required.get(key_name, True) and (key_name in present_keys)

        if not key_types:
            # All returns had only unpacking; fallback to generic wrapper
            model_name = _unique_name(func_name + "Result", used_names)
            model_text = f"class {model_name}(TypedDictModel):\n    pass\n"
            replacements = []
            for ret, _dict_node, segment in returns:
                r = f"{model_name}.model_validate({segment})"
                replacements.append((ret.value.lineno, ret.value.col_offset, ret.value.end_lineno, ret.value.end_col_offset, r))
            out[func_name] = (model_text, replacements)
            continue

        model_name = _unique_name(func_name + "Result", used_names)
        lines = [f"class {model_name}(TypedDictModel):"]
        for key_name in sorted(key_types):
            types = key_types[key_name]
            if len(types) == 1:
                field_type = types.pop()
            else:
                # Union of types; simplify common cases
                types.discard("Any")
                if not types:
                    field_type = "Any"
                elif len(types) == 1:
                    field_type = types.pop()
                else:
                    field_type = " | ".join(sorted(types))

            if not key_required.get(key_name, True):
                field_type = f"{field_type} | None"
                default = " = None"
            else:
                default = ""

            # Sanitize key for use as a Python identifier (though Pydantic handles any string key)
            lines.append(f"    {key_name}: {field_type}{default}")

        model_text = "\n".join(lines) + "\n"

        replacements = []
        for ret, _dict_node, segment in returns:
            r = f"{model_name}.model_validate({segment})"
            replacements.append((ret.value.lineno, ret.value.col_offset, ret.value.end_lineno, ret.value.end_col_offset, r))

        out[func_name] = (model_text, replacements)

    return out


def _unique_name(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    i = 1
    while f"{base}{i}" in used:
        i += 1
    name = f"{base}{i}"
    used.add(name)
    return name


def _apply_changes(source: str, models_text: str, replacements: list[tuple[int, int, int, int, str]]) -> str:
    """Apply replacements and prepend model definitions + import."""
    lines = source.split("\n")

    # Sort replacements by line descending so earlier edits don't shift later ones
    replacements = sorted(replacements, key=lambda x: (x[0], x[1]), reverse=True)

    for start_line, start_col, end_line, end_col, repl in replacements:
        sl = start_line - 1
        el = end_line - 1
        if sl == el:
            line = lines[sl]
            lines[sl] = line[:start_col] + repl + line[end_col:]
        else:
            start_text = lines[sl][:start_col]
            end_text = lines[el][end_col:]
            lines[sl] = start_text + repl + end_text
            for i in range(sl + 1, el + 1):
                lines[i] = ""

    # Insert import if missing
    has_import = "from shared.models.typed_dict import TypedDictModel" in source
    if not has_import:
        # Use AST to find last top-level import for reliable insertion
        try:
            mod_tree = ast.parse(source)
        except SyntaxError:
            mod_tree = None

        last_import_line = -1
        if mod_tree:
            for node in mod_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_line = max(last_import_line, getattr(node, "end_lineno", node.lineno) - 1)

        if last_import_line >= 0:
            lines.insert(last_import_line + 1, "from shared.models.typed_dict import TypedDictModel")
        else:
            # Insert after module docstring if present
            insert_at = 0
            if lines and lines[0].strip().startswith('"""'):
                for i, line in enumerate(lines):
                    if '"""' in line and i > 0:
                        insert_at = i + 1
                        break
            lines.insert(insert_at, "from shared.models.typed_dict import TypedDictModel")

    # Insert model definitions after import (or after last import)
    # Find the line we just inserted
    import_line = -1
    for i, line in enumerate(lines):
        if "from shared.models.typed_dict import TypedDictModel" in line:
            import_line = i
            break

    if models_text.strip():
        model_lines = models_text.rstrip().split("\n")
        # Insert two blank lines after import, then models
        for ml in reversed(model_lines):
            lines.insert(import_line + 1, ml)
        lines.insert(import_line + 1, "")
        lines.insert(import_line + 1, "")

    new_source = "\n".join(lines)
    # Collapse excessive blank lines created by multi-line replacements
    new_source = re.sub(r"\n{4,}", "\n\n\n", new_source)
    return new_source


def process_file(path: Path) -> int:
    """Process a single file. Returns number of dict returns converted."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0

    try:
        tree = ast.parse(source)
    except SyntaxError:
        print(f"  SKIP (syntax error): {path}", file=sys.stderr)
        return 0

    grouped = _gather_returns(tree, source)
    if not grouped:
        return 0

    models = _build_models(grouped)
    all_models_text = "\n".join(mt for mt, _ in models.values())
    all_replacements = []
    for _func_name, (_mt, reps) in models.items():
        all_replacements.extend(reps)

    if not all_replacements:
        return 0

    new_source = _apply_changes(source, all_models_text, all_replacements)
    path.write_text(new_source, encoding="utf-8")
    return len(all_replacements)


def _files_from_lint() -> list[Path]:
    """Run the platform contract linter and extract files with raw_dict_agent_return."""
    lint_path = PROJECT_ROOT / "scripts" / "ci" / "platform_contract_lint.py"
    import subprocess
    result = subprocess.run(
        [sys.executable, str(lint_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    files: set[Path] = set()
    pattern = re.compile(r"^WARN:\s+(\S+)::\d+\s+\[raw_dict_agent_return\]")
    for line in result.stderr.splitlines():
        m = pattern.match(line)
        if m:
            files.add(PROJECT_ROOT / m.group(1))
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk convert raw dict returns to typed models")
    parser.add_argument("files", nargs="*", help="Python files to process")
    parser.add_argument("--from-lint", action="store_true", help="Process all files flagged by platform_contract_lint.py")
    args = parser.parse_args()

    files: list[Path] = []
    if args.from_lint:
        files = _files_from_lint()
        print(f"Found {len(files)} files from linter")
    else:
        files = [Path(f) for f in args.files]

    if not files:
        print("No files to process.")
        sys.exit(0)

    total_converted = 0
    for f in files:
        rel = f.relative_to(PROJECT_ROOT) if f.is_relative_to(PROJECT_ROOT) else f
        count = process_file(f)
        if count:
            print(f"  + {rel}: {count} dict returns converted")
            total_converted += count

    print(f"\nTotal converted: {total_converted}")


if __name__ == "__main__":
    main()
