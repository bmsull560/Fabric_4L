import os, re, ast

def extract_defs(content):
    tree = ast.parse(content)
    lines = content.splitlines()
    defs = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            start = node.lineno - 1
            end = node.end_lineno
            defs[node.name] = '\n'.join(lines[start:end])
    return defs

# === 1. identity/models.py ===
def merge_models():
    with open('shared/identity/models.py', 'r', encoding='utf-8', errors='ignore') as f:
        root_content = f.read()
    with open('value-fabric/shared/identity/models.py', 'r', encoding='utf-8', errors='ignore') as f:
        vf_content = f.read()
    
    root_defs = extract_defs(root_content)
    vf_defs = extract_defs(vf_content)
    
    only_root = set(root_defs.keys()) - set(vf_defs.keys())
    if only_root:
        merged = vf_content.rstrip() + '\n\n# Merged from root shared/identity/models.py\n' + '\n\n'.join(root_defs[n] for n in sorted(only_root)) + '\n'
    else:
        merged = vf_content
    
    with open('packages/shared/src/value_fabric/shared/identity/models.py', 'w', encoding='utf-8') as f:
        f.write(merged)
    print(f"Merged identity/models.py: added {only_root}")

# === 2. identity/dependencies.py ===
def merge_dependencies():
    with open('shared/identity/dependencies.py', 'r', encoding='utf-8', errors='ignore') as f:
        root_content = f.read()
    with open('value-fabric/shared/identity/dependencies.py', 'r', encoding='utf-8', errors='ignore') as f:
        vf_content = f.read()
    
    root_defs = extract_defs(root_content)
    vf_defs = extract_defs(vf_content)
    
    only_root = set(root_defs.keys()) - set(vf_defs.keys())
    if only_root:
        merged = vf_content.rstrip() + '\n\n# Merged from root shared/identity/dependencies.py\n' + '\n\n'.join(root_defs[n] for n in sorted(only_root)) + '\n'
    else:
        merged = vf_content
    
    with open('packages/shared/src/value_fabric/shared/identity/dependencies.py', 'w', encoding='utf-8') as f:
        f.write(merged)
    print(f"Merged identity/dependencies.py: added {only_root}")

# === 3. identity/vault_check.py ===
def merge_vault_check():
    with open('shared/identity/vault_check.py', 'r', encoding='utf-8', errors='ignore') as f:
        root_content = f.read()
    with open('value-fabric/shared/identity/vault_check.py', 'r', encoding='utf-8', errors='ignore') as f:
        vf_content = f.read()
    
    root_defs = extract_defs(root_content)
    vf_defs = extract_defs(vf_content)
    
    only_root = set(root_defs.keys()) - set(vf_defs.keys())
    if only_root:
        merged = vf_content.rstrip() + '\n\n# Merged from root shared/identity/vault_check.py\n' + '\n\n'.join(root_defs[n] for n in sorted(only_root)) + '\n'
    else:
        merged = vf_content
    
    with open('packages/shared/src/value_fabric/shared/identity/vault_check.py', 'w', encoding='utf-8') as f:
        f.write(merged)
    print(f"Merged identity/vault_check.py: added {only_root}")

# === 4. models/typed_dict.py ===
def write_merged_typed_dict():
    content = '''"""TypedDict-style model base for shared package.

Provides a Pydantic BaseModel subclass used across the codebase
for type-safe dictionary-like response models.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class TypedDictModel(BaseModel):
    """Base model for typed-dict style response objects.

    Subclass this to define structured response shapes that can be
    validated with `.model_validate()` and serialized with `.model_dump()`.

    Supports dict-like access via ``[]``, ``in``, ``.get()``,
    iteration over keys/values/items, and assignment.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        arbitrary_types_allowed=True,
        strict=False,
    )

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for ``key`` if it exists, else ``default``."""
        return getattr(self, key, default)

    def __iter__(self):
        """Iterate over field names."""
        return iter(self.model_dump())

    def keys(self):
        return self.model_dump().keys()

    def values(self):
        return self.model_dump().values()

    def items(self):
        return self.model_dump().items()

    def __len__(self) -> int:
        """Return the number of fields."""
        return len(self.model_dump())
'''
    with open('packages/shared/src/value_fabric/shared/models/typed_dict.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Wrote merged models/typed_dict.py")

# === 5. audit/__init__.py ===
def merge_audit_init():
    with open('value-fabric/shared/audit/__init__.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    content = content.replace(
        'from .models import AuditAction, AuditEvent, AuditOutcome',
        'from .models import AuditAction, AuditEvent, AuditOutcome, TenantResolvedDetails, TenantContextSetDetails'
    )
    
    # Update __all__
    content = content.replace(
        '__all__ = [\n    "AuditAction",',
        '__all__ = [\n    "TenantResolvedDetails",\n    "TenantContextSetDetails",\n    "AuditAction",'
    )
    
    with open('packages/shared/src/value_fabric/shared/audit/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Merged audit/__init__.py")

# === 6. identity/__init__.py ===
def merge_identity_init():
    with open('value-fabric/shared/identity/__init__.py', 'r', encoding='utf-8', errors='ignore') as f:
        vf = f.read()
    
    # Add root-only imports
    extra_imports = '''from .dependencies import (
    require_tenant_admin,
    require_super_admin,
)
from .vault_check import check_vault_health, resolve_vault_secret
'''
    
    # Insert before __all__
    vf = vf.replace('__all__ = [', extra_imports + '__all__ = [')
    
    # Add to __all__
    extra_all = '''    # Dependencies (merged from root)
    "require_tenant_admin",
    "require_super_admin",
    # Vault (merged from root)
    "check_vault_health",
    "resolve_vault_secret",
    # Models (merged from root)
    "TenantStatus",
    "UserStatus",
    "TenantCreateRequest",
    "TenantUpdateRequest",
    "UserInviteRequest",
    "UserUpdateRequest",
    "APIKeyCreateRequest",
    "APIKeyCreateResponse",
'''
    
    vf = vf.replace(
        '    # Context\n    "RequestContext",',
        extra_all + '    # Context\n    "RequestContext",'
    )
    
    with open('packages/shared/src/value_fabric/shared/identity/__init__.py', 'w', encoding='utf-8') as f:
        f.write(vf)
    print("Merged identity/__init__.py")

# === 7. security/__init__.py ===
def write_security_init():
    content = '''"""Shared security middleware for input validation and sanitization.

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
        f.write(content)
    print("Wrote security/__init__.py")

# === 8. models/__init__.py ===
def write_models_init():
    content = '''"""Shared models package for Value Fabric."""

from .typed_dict import TypedDictModel

__all__ = ["TypedDictModel"]
'''
    with open('packages/shared/src/value_fabric/shared/models/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Wrote models/__init__.py")

# === 9. secrets/__init__.py ===
def write_secrets_init():
    # Root has no __init__.py, VF has one
    with open('value-fabric/shared/secrets/__init__.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    with open('packages/shared/src/value_fabric/shared/secrets/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Copied secrets/__init__.py from VF")

# Run all
if __name__ == '__main__':
    merge_models()
    merge_dependencies()
    merge_vault_check()
    write_merged_typed_dict()
    merge_audit_init()
    merge_identity_init()
    write_security_init()
    write_models_init()
    write_secrets_init()
    print("\nAll merges complete.")
