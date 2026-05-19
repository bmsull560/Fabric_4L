#!/usr/bin/env python3
"""Resolve all git merge conflicts in the repository by keeping the last (theirs) side.

Handles nested conflict markers. Usage:
    python scripts/resolve_all_conflicts.py [--dry-run]
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def resolve_nested_conflicts(content: str) -> str:
    """Strip all conflict markers, keeping the last side of each conflict.
    
    Handles nested conflicts by using a stack-based parser.
    """
    lines = content.splitlines(keepends=True)
    result = []
    
    # Stack of conflict frames. Each frame: [side0_content, side1_content, ...]
    # side0 = before first =======, side1 = after first ======= before >>>>>>>, etc.
    stack: list[list[list[str]]] = []
    current_side_content: list[str] = []
    
    for line in lines:
        stripped = line.lstrip()
        
        if stripped.startswith("<<<<<<< "):
            # Start of a new conflict block
            # Save current content to result (it's outside the conflict)
            if current_side_content and not stack:
                result.extend(current_side_content)
                current_side_content = []
            
            # Push new frame
            stack.append([current_side_content])
            current_side_content = []
            
        elif stripped.startswith("======="):
            # End of current side, start of next side
            if not stack:
                # Malformed - just keep it
                current_side_content.append(line)
                continue
            
            # Save current side to the frame
            stack[-1].append(current_side_content)
            current_side_content = []
            
        elif stripped.startswith(">>>>>>> "):
            # End of conflict block
            if not stack:
                # Malformed - just keep it
                current_side_content.append(line)
                continue
            
            # Save the last side
            stack[-1].append(current_side_content)
            
            # Pop the frame
            frame = stack.pop()
            
            # The resolved content for this conflict is the LAST side
            resolved = frame[-1] if frame else []
            
            if stack:
                # We're inside a parent conflict - append to the parent's current side
                current_side_content = resolved
            else:
                # Top-level conflict - append to result
                current_side_content = resolved
                
        else:
            # Regular line
            current_side_content.append(line)
    
    # Flush remaining content
    if current_side_content and not stack:
        result.extend(current_side_content)
    
    return "".join(result)


def find_conflicted_files(repo_root: Path) -> list[Path]:
    """Find all files containing merge conflict markers."""
    extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml", ".md", ".rego", ".mjs"}
    exclude_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", "dist", "build", ".windsurf", ".mypy_cache", ".ruff_cache", ".vite", "artifacts", "audit-output"}
    
    files = []
    for path in repo_root.rglob("*"):
        if path.is_dir():
            if path.name in exclude_dirs:
                continue
        if path.suffix in extensions:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                if any(line.lstrip().startswith("<<<<<<< ") for line in content.splitlines()):
                    files.append(path)
            except (UnicodeDecodeError, OSError):
                continue
    
    return sorted(files)


def main():
    dry_run = "--dry-run" in sys.argv
    
    files = find_conflicted_files(REPO_ROOT)
    
    if not files:
        print("No files with merge conflicts found.")
        return 0
    
    print(f"Found {len(files)} files with merge conflicts:")
    for f in files:
        rel = f.relative_to(REPO_ROOT)
        print(f"  - {rel}")
    
    if dry_run:
        print("\nDry run - no changes made.")
        return 0
    
    print("\nResolving conflicts (keeping 'theirs' side)...")
    resolved_count = 0
    
    for filepath in files:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        resolved = resolve_nested_conflicts(content)
        
        if resolved != content:
            filepath.write_text(resolved, encoding="utf-8")
            rel = filepath.relative_to(REPO_ROOT)
            print(f"  Resolved: {rel}")
            resolved_count += 1
        else:
            rel = filepath.relative_to(REPO_ROOT)
            print(f"  Unchanged: {rel}")
    
    print(f"\nResolved conflicts in {resolved_count} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
