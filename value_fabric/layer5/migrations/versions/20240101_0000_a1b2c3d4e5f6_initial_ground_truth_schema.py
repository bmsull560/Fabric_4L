"""Compatibility shim for canonical layer5_ground_truth.migrations.versions.20240101_0000_a1b2c3d4e5f6_initial_ground_truth_schema."""

from importlib import import_module as _import_module

_CANONICAL_MODULE = "layer5_ground_truth.migrations.versions.20240101_0000_a1b2c3d4e5f6_initial_ground_truth_schema"
_module = _import_module(_CANONICAL_MODULE)
for _name in dir(_module):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_module, _name)

__all__ = [_name for _name in globals() if not _name.startswith("_")]
