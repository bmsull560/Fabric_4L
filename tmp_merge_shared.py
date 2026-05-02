import os, re, ast

def extract_classes_and_functions(source_path):
    """Extract top-level class and function names from a Python file."""
    with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    tree = ast.parse(content)
    names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
    return names, content

def merge_models(root_path, vf_path, out_path):
    """Merge identity/models.py: take VF base, append root-only classes."""
    root_names, root_content = extract_classes_and_functions(root_path)
    vf_names, vf_content = extract_classes_and_functions(vf_path)
    
    only_in_root = root_names - vf_names
    if not only_in_root:
        # Just copy VF
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(vf_content)
        return
    
    # Parse root content to extract only the missing classes
    tree = ast.parse(root_content)
    lines = root_content.splitlines()
    
    extracts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in only_in_root:
            start_line = node.lineno - 1
            end_line = node.end_lineno
            extract = '\n'.join(lines[start_line:end_line])
            extracts.append(extract)
    
    merged = vf_content.rstrip() + '\n\n# Merged from root shared/identity/models.py\n' + '\n\n'.join(extracts) + '\n'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(merged)
    print(f"Merged {out_path}: added {only_in_root}")

# Merge identity/models.py
merge_models(
    'shared/identity/models.py',
    'value-fabric/shared/identity/models.py',
    'packages/shared/src/value_fabric/shared/identity/models.py'
)

# For other DIFF files, keep VF version (already copied)
# Now handle __init__.py merges

# audit/__init__.py
with open('value-fabric/shared/audit/__init__.py', 'r', encoding='utf-8') as f:
    vf_audit_init = f.read()

# Add root-only exports
audit_init = vf_audit_init.replace(
    '__all__ = [',
    '__all__ = [\n    "TenantResolvedDetails",\n    "TenantContextSetDetails",\n'
)
audit_init = audit_init.replace(
    'from .models import AuditAction, AuditEvent, AuditOutcome',
    'from .models import AuditAction, AuditEvent, AuditOutcome, TenantResolvedDetails, TenantContextSetDetails'
)
with open('packages/shared/src/value_fabric/shared/audit/__init__.py', 'w', encoding='utf-8') as f:
    f.write(audit_init)
print("Merged audit/__init__.py")

# security/__init__.py
sec_init = '''"""Shared security middleware for input validation and sanitization.

This package provides a centralized SecurityMiddleware implementation
with per-layer configuration support.
"""

from .middleware import (
    SecurityConfig,
    SecurityMiddleware,
    SecurityValidator,
    add_security_middleware,
    SQL_INJECTION_PATTERNS,
    XSS_PATTERNS,
    NOSQL_INJECTION_PATTERNS,
)
from .config import SecurityConfig as RootSecurityConfig

__all__ = [
    "SecurityConfig",
    "SecurityMiddleware",
    "SecurityValidator",
    "add_security_middleware",
    "SQL_INJECTION_PATTERNS",
    "XSS_PATTERNS",
    "NOSQL_INJECTION_PATTERNS",
]
'''
with open('packages/shared/src/value_fabric/shared/security/__init__.py', 'w', encoding='utf-8') as f:
    f.write(sec_init)
print("Merged security/__init__.py")

# models/__init__.py - copy from VF (already there, just ensure it exists)
models_init = '''"""Shared models package for Value Fabric."""

from .typed_dict import TypedDictModel

__all__ = ["TypedDictModel"]
'''
with open('packages/shared/src/value_fabric/shared/models/__init__.py', 'w', encoding='utf-8') as f:
    f.write(models_init)
print("Wrote models/__init__.py")

print("Merge complete.")
