"""Compatibility shim for canonical layer5_ground_truth.migrations.versions.002_add_rls_policies."""

from importlib import import_module as _import_module

_CANONICAL_MODULE = "layer5_ground_truth.migrations.versions.002_add_rls_policies"
_module = _import_module(_CANONICAL_MODULE)
for _name in dir(_module):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_module, _name)

__all__ = [_name for _name in globals() if not _name.startswith("_")]
