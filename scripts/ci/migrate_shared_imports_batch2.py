#!/usr/bin/env python3
"""
Migrate legacy shared imports to value_fabric.shared imports - Batch 2: Test Files

Scope: tests/, services/*/tests/, packages/*/tests/, value-fabric/tests/ (legacy, being deleted)
Rules:
- Replace: from shared.X import Y → from value_fabric.shared.X import Y
- Replace: import shared.X as X → import value_fabric.shared.X as X
- Avoid: import value_fabric.shared as shared, root shared package, compatibility shim, star imports
- Preserve tests that intentionally assert import shared fails
"""

import re
from pathlib import Path


def should_migrate_file(file_path: Path, repo_root: Path) -> bool:
    """Determine if a file should be migrated in Batch 2 (test files only)."""
    try:
        rel_path = file_path.relative_to(repo_root)
    except ValueError:
        return False
    
    path_str = str(rel_path).replace("\\", "/")
    
    # Include only test files
    if "/tests/" not in path_str:
        return False
    
    # Exclude the boundary test that intentionally checks legacy imports fail
    if "test_shared_import_boundary.py" in path_str:
        return False
    
    return True


def migrate_imports(content: str) -> tuple[str, int]:
    """Migrate shared imports to value_fabric.shared imports. Returns (new_content, changes_made)."""
    changes = 0
    
    # Pattern 1: from shared.X import Y
    pattern1 = re.compile(r'\bfrom shared\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+import')
    
    def replace_pattern1(match):
        nonlocal changes
        changes += 1
        return f'from value_fabric.shared.{match.group(1)} import'
    
    content = pattern1.sub(replace_pattern1, content)
    
    # Pattern 2: import shared.X as Y
    pattern2 = re.compile(r'\bimport shared\.([a-zA-Z_][a-zA-Z0-9_.]*)\s+as\s+([a-zA-Z_][a-zA-Z0-9_]*)')
    
    def replace_pattern2(match):
        nonlocal changes
        changes += 1
        return f'import value_fabric.shared.{match.group(1)} as {match.group(2)}'
    
    content = pattern2.sub(replace_pattern2, content)
    
    # Pattern 3: import shared.X (without as)
    pattern3 = re.compile(r'\bimport shared\.([a-zA-Z_][a-zA-Z0-9_.]*)\b')
    
    def replace_pattern3(match):
        nonlocal changes
        changes += 1
        return f'import value_fabric.shared.{match.group(1)}'
    
    content = pattern3.sub(replace_pattern3, content)
    
    return content, changes


def main():
    repo_root = Path(__file__).parent.parent.parent
    total_changes = 0
    files_changed = []
    
    # Find all Python files in scope
    for py_file in repo_root.rglob("*.py"):
        if not should_migrate_file(py_file, repo_root):
            continue
        
        try:
            content = py_file.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            continue
        
        # Check if file has shared imports
        if "from shared." not in content and "import shared." not in content:
            continue
        
        # Migrate imports
        new_content, changes = migrate_imports(content)
        
        if changes > 0:
            py_file.write_text(new_content, encoding="utf-8")
            total_changes += changes
            files_changed.append(str(py_file.relative_to(repo_root)))
    
    print(f"Migrated {total_changes} imports in {len(files_changed)} test files")
    print("\nFiles changed:")
    for file_path in files_changed:
        print(f"  {file_path}")


if __name__ == "__main__":
    main()
