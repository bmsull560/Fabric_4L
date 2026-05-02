import os, re

# Pattern to match imports from shared.*
SHARED_IMPORT_RE = re.compile(
    r'^from shared\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*) import',
    re.MULTILINE
)

IMPORT_SHARED_RE = re.compile(
    r'^import shared\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
    re.MULTILINE
)

def update_file(path, is_internal_shared=False):
    """Update imports in a single file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"  Error reading {path}: {e}")
        return 0
    
    original = content
    changes = 0
    
    if is_internal_shared:
        # Within the shared package, convert to absolute value_fabric.shared imports
        def repl(m):
            return f'from value_fabric.shared.{m.group(1)} import'
        content, count = SHARED_IMPORT_RE.subn(repl, content)
        changes += count
        
        content, count = IMPORT_SHARED_RE.subn(
            lambda m: f'import value_fabric.shared.{m.group(1)}',
            content
        )
        changes += count
    else:
        # External files: replace from shared.X with from value_fabric.shared.X
        content, count = SHARED_IMPORT_RE.subn(
            lambda m: f'from value_fabric.shared.{m.group(1)} import',
            content
        )
        changes += count
        
        content, count = IMPORT_SHARED_RE.subn(
            lambda m: f'import value_fabric.shared.{m.group(1)}',
            content
        )
        changes += count
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes

def main():
    total_changes = 0
    files_changed = 0
    
    # 1. Update imports within the new shared package
    print("Updating internal shared package imports...")
    shared_pkg = 'packages/shared/src/value_fabric/shared'
    for root, dirs, files in os.walk(shared_pkg):
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            changes = update_file(path, is_internal_shared=True)
            if changes:
                total_changes += changes
                files_changed += 1
                print(f"  {path}: {changes} changes")
    
    # 2. Update imports across the entire codebase
    print("\nUpdating external imports...")
    skip_dirs = {
        '.git', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache',
        '.ruff_cache', 'dist', 'build', 'prototypes', 'reports', 'packages',
        'value_fabric',  # Skip junction content
    }
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            changes = update_file(path, is_internal_shared=False)
            if changes:
                total_changes += changes
                files_changed += 1
                print(f"  {path}: {changes} changes")
    
    print(f"\nTotal: {total_changes} changes in {files_changed} files")

if __name__ == '__main__':
    main()
