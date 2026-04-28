"""CI gate: Detect tenant boundary violations before they reach production.

This script fails the build if any direct header access patterns are detected.
Run in CI with: python scripts/ci/boundary_check.py

Exit codes:
    0: No violations detected
    1: Violations found (CI gate fails)
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# Violation patterns - only detect READING headers (incoming requests)
# NOT setting headers on outgoing requests (headers['X-Tenant-ID'] = value is OK)
# Uses case-insensitive header name matching to catch all variants:
#   X-Tenant-ID, x-tenant-id, X-Tenant-Id, X-TENANT-ID, HTTP_X_TENANT_ID
VIOLATION_PATTERNS = [
    # headers['X-Tenant-ID'] used as value (not assignment) - case-insensitive header name
    r"headers\s*\[\s*['\"][Xx]-[Tt][Ee][Nn][Aa][Nn][Tt]-[Ii][Dd]['\"]\s*\](?!\s*=)",
    # headers.get('X-Tenant-ID') - case-insensitive header name
    r"headers\.get\s*\(\s*['\"][Xx]-[Tt][Ee][Nn][Aa][Nn][Tt]-[Ii][Dd]['\"]",
    # request.headers['X-Tenant-ID'] used as value - case-insensitive header name
    r"request\.headers\s*\[\s*['\"][Xx]-[Tt][Ee][Nn][Aa][Nn][Tt]-[Ii][Dd]['\"]\s*\](?!\s*=)",
    # request.headers.get('X-Tenant-ID') - case-insensitive header name
    r"request\.headers\.get\s*\(\s*['\"][Xx]-[Tt][Ee][Nn][Aa][Nn][Tt]-[Ii][Dd]['\"]",
    # req.headers patterns - case-insensitive header name
    r"req\.headers\s*\[\s*['\"][Xx]-[Tt][Ee][Nn][Aa][Nn][Tt]-[Ii][Dd]['\"]\s*\](?!\s*=)",
    r"req\.headers\.get\s*\(\s*['\"][Xx]-[Tt][Ee][Nn][Aa][Nn][Tt]-[Ii][Dd]['\"]",
    # WSGI convention: HTTP_X_TENANT_ID
    r"environ\[[\'\"]HTTP_[Xx]_[Tt][Ee][Nn][Aa][Nn][Tt]_[Ii][Dd][\'\"]\]",
]

# Allowed paths (internal boundary implementations and security validators)
ALLOWED_PATHS = [
    "shared/boundaries/tenant_boundary.py",
    "shared/identity/middleware.py",
    "shared/identity/context.py",
    "shared/security/dil_auth.py",  # Security validator - compares header against context
]


def is_allowed_path(filepath: Path) -> bool:
    """Check if file is in allowed list."""
    path_str = str(filepath).replace("\\", "/")
    return any(allowed in path_str for allowed in ALLOWED_PATHS)


def has_boundary_import(content: str) -> bool:
    """Check if file uses boundary imports via AST parsing.
    
    Avoids false positives from comments or string literals.
    """
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and ('shared.boundaries' in node.module or node.module == 'shared.boundaries'):
                    for alias in node.names:
                        if alias.name in ('require_tenant_from_request', 'require_tenant_context'):
                            return True
    except SyntaxError:
        pass
    return False


def find_violations_in_file(filepath: Path) -> list[dict]:
    """Find all violations in a file."""
    if is_allowed_path(filepath):
        return []
    
    violations = []
    try:
        content = filepath.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Pre-compute if file already uses boundary imports (AST-based, not substring)
        file_has_boundary = has_boundary_import(content)
        
        for line_num, line in enumerate(lines, 1):
            for pattern in VIOLATION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if file already uses boundary imports properly
                    if file_has_boundary:
                        continue
                    violations.append({
                        'line': line_num,
                        'content': line.strip(),
                        'pattern': pattern,
                    })
                    break  # One violation per line is enough
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {filepath}: {e}")
    
    return violations


def main():
    """Run boundary check and exit with appropriate code."""
    root = Path("value-fabric")
    if not root.exists():
        print("Error: value-fabric directory not found")
        sys.exit(1)
    
    print("=" * 60)
    print("TENANT BOUNDARY SECURITY CHECK")
    print("=" * 60)
    print()
    
    all_violations: dict[Path, list[dict]] = {}
    
    for filepath in root.rglob("*.py"):
        # Skip virtual environments and third-party packages
        path_str = str(filepath).replace("\\", "/")
        if "/.venv/" in path_str or "/site-packages/" in path_str:
            continue
        violations = find_violations_in_file(filepath)
        if violations:
            all_violations[filepath] = violations
    
    if not all_violations:
        print("✓ No tenant boundary violations detected")
        print()
        print("All code properly uses shared.boundaries for tenant context")
        sys.exit(0)
    
    # Print violations
    total = 0
    for filepath, violations in sorted(all_violations.items()):
        print(f"\n{filepath}")
        for v in violations:
            print(f"  Line {v['line']}: {v['content'][:60]}")
            total += 1
    
    print()
    print("=" * 60)
    print(f"FAIL: {len(all_violations)} files with {total} boundary violations")
    print("=" * 60)
    print()
    print("Direct header access is prohibited. Use:")
    print("  from shared.boundaries import require_tenant_from_request")
    print()
    print("To fix automatically:")
    print("  python scripts/fix_tenant_boundary_violations.py --apply")
    print()
    
    sys.exit(1)


if __name__ == "__main__":
    main()
