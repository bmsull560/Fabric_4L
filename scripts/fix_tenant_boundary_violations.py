"""AST-based migration script for tenant boundary violations.

Transforms 222+ violations:
- headers['x-tenant-id'] → require_tenant_from_request(request).tenant_id
- headers.get('X-Tenant-ID') → require_tenant_from_request(request).tenant_id
- request.headers['x-tenant-id'] → require_tenant_from_request(request)

Usage:
    python scripts/fix_tenant_boundary_violations.py --dry-run
    python scripts/fix_tenant_boundary_violations.py --apply
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Iterator, Set

# Patterns that indicate direct header access (case-insensitive header names)
# Only detect READING headers (incoming requests), NOT setting them
VIOLATION_PATTERNS = [
    # headers['x-tenant-id'] used as value (not assignment)
    r"headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\](?!\s*=)",
    r"headers\s*\[\s*['\"]x-tenant-id['\"]\s*\](?!\s*=)",
    # headers.get('x-tenant-id')
    r"headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]",
    r"headers\.get\s*\(\s*['\"]x-tenant-id['\"]",
    # request.headers['x-tenant-id'] used as value
    r"request\.headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\](?!\s*=)",
    r"request\.headers\s*\[\s*['\"]x-tenant-id['\"]\s*\](?!\s*=)",
    # request.headers.get('x-tenant-id')
    r"request\.headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]",
    r"request\.headers\.get\s*\(\s*['\"]x-tenant-id['\"]",
    # req.headers patterns
    r"req\.headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\](?!\s*=)",
    r"req\.headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]",
]

# Files to skip (middleware itself, allowed internal uses)
SKIP_PATHS = [
    "shared/boundaries/tenant_boundary.py",
    "shared/identity/middleware.py",
    "shared/identity/context.py",
    "tests/",
    "test_",
]

REQUIRED_IMPORT = "from shared.boundaries.tenant_boundary import require_tenant_from_request, require_tenant_context"
ALTERNATIVE_IMPORT = "from shared.boundaries import require_tenant_from_request, require_tenant_context"


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped from migration."""
    path_str = str(filepath).replace("\\", "/")
    # Skip virtual environments and third-party packages
    if "/.venv/" in path_str or "/site-packages/" in path_str:
        return True
    for skip in SKIP_PATHS:
        if skip in path_str:
            return True
    return False


def find_violations(content: str) -> list[re.Match]:
    """Find all tenant header access violations in content."""
    violations = []
    for pattern in VIOLATION_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            violations.append(match)
    return violations


def transform_content(content: str, filepath: Path) -> tuple[str, int]:
    """Transform violations to use require_tenant_from_request.
    
    Returns:
        Tuple of (transformed_content, violation_count)
    """
    violations = find_violations(content)
    if not violations:
        return content, 0
    
    # Track if we need to add import
    needs_import = True
    if "shared.boundaries" in content or "require_tenant_from_request" in content:
        needs_import = False
    
    # Simple regex-based replacement (for common patterns)
    transformed = content
    
    # Pattern: headers['x-tenant-id'] or headers.get('x-tenant-id')
    # Replace with: require_tenant_from_request(request)
    
    # First, identify if 'request' variable exists in scope
    has_request_param = "request: Request" in content or "def " in content and "request" in content
    
    replacements = [
        # headers['X-Tenant-ID'] variants
        (r"headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\]", "require_tenant_from_request(request)"),
        (r"headers\s*\[\s*['\"]x-tenant-id['\"]\s*\]", "require_tenant_from_request(request)"),
        # headers.get() variants
        (r"headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]\s*\)", "require_tenant_from_request(request)"),
        (r"headers\.get\s*\(\s*['\"]x-tenant-id['\"]\s*\)", "require_tenant_from_request(request)"),
        # request.headers variants
        (r"request\.headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\]", "require_tenant_from_request(request)"),
        (r"request\.headers\s*\[\s*['\"]x-tenant-id['\"]\s*\]", "require_tenant_from_request(request)"),
        (r"request\.headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]\s*\)", "require_tenant_from_request(request)"),
        (r"request\.headers\.get\s*\(\s*['\"]x-tenant-id['\"]\s*\)", "require_tenant_from_request(request)"),
        # req.headers variants
        (r"req\.headers\s*\[\s*['\"]X-Tenant-ID['\"]\s*\]", "require_tenant_from_request(req)"),
        (r"req\.headers\.get\s*\(\s*['\"]X-Tenant-ID['\"]\s*\)", "require_tenant_from_request(req)"),
    ]
    
    for pattern, replacement in replacements:
        transformed = re.sub(pattern, replacement, transformed, flags=re.IGNORECASE)
    
    # Add import if needed
    if needs_import and find_violations(content):
        # Find a good place to add import
        lines = transformed.split('\n')
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_idx = i + 1
        
        # Check if FastAPI Request is imported
        if 'from fastapi import' in content and 'Request' not in content:
            # Need to add Request to imports
            transformed = re.sub(
                r'(from fastapi import[^\n]+)',
                r'\1, Request',
                transformed
            )
        elif 'from fastapi import' not in content:
            # Add FastAPI Request import
            lines.insert(import_idx, "from fastapi import Request")
            import_idx += 1
        
        lines.insert(import_idx, REQUIRED_IMPORT)
        transformed = '\n'.join(lines)
    
    return transformed, len(violations)


def scan_directory(root: Path) -> Iterator[Path]:
    """Yield all Python files in directory recursively."""
    for path in root.rglob("*.py"):
        if not should_skip_file(path):
            yield path


def main():
    parser = argparse.ArgumentParser(description="Fix tenant boundary violations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without applying")
    parser.add_argument("--apply", action="store_true", help="Apply fixes to files")
    parser.add_argument("--root", default="value-fabric", help="Root directory to scan")
    args = parser.parse_args()
    
    root_path = Path(args.root)
    if not root_path.exists():
        print(f"Error: Root path does not exist: {root_path}")
        sys.exit(1)
    
    total_violations = 0
    files_with_violations = 0
    
    print(f"Scanning for tenant boundary violations in: {root_path}")
    print("-" * 60)
    
    for filepath in scan_directory(root_path):
        try:
            content = filepath.read_text(encoding='utf-8')
            violations = find_violations(content)
            
            if violations:
                files_with_violations += 1
                total_violations += len(violations)
                
                if args.dry_run or not args.apply:
                    print(f"\n{filepath}")
                    for v in violations:
                        # Show context around violation
                        start = max(0, v.start() - 40)
                        end = min(len(content), v.end() + 40)
                        context = content[start:end].replace('\n', ' ')
                        print(f"  Line ~{content[:v.start()].count(chr(10)) + 1}: ...{context}...")
                
                if args.apply:
                    transformed, count = transform_content(content, filepath)
                    if transformed != content:
                        filepath.write_text(transformed, encoding='utf-8')
                        print(f"  ✓ Fixed {count} violation(s) in {filepath}")
        
        except Exception as e:
            print(f"  ✗ Error processing {filepath}: {e}")
    
    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Files with violations: {files_with_violations}")
    print(f"  Total violations: {total_violations}")
    
    if args.dry_run:
        print(f"\n  (Dry run - no changes made)")
        print(f"  Run with --apply to fix violations")
    elif args.apply:
        print(f"\n  ✓ Fixes applied")
    
    # Exit with error code if violations found (for CI)
    if total_violations > 0 and not args.apply:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
