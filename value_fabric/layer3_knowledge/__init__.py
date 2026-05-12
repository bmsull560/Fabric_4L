"""Compatibility namespace for legacy Layer 3 test imports.

The active compatibility package is ``value_fabric.layer3``.  Some historical
contract and service tests still import ``value_fabric.layer3_knowledge.src.*``;
this shim maps that package shape to the Layer 3 source tree without requiring
runner-specific path mutation.
"""

from __future__ import annotations

__all__: list[str] = []

import warnings

warnings.warn(
    "layer3_knowledge is deprecated; migrate imports to value_fabric.layer3 (compatibility shim scheduled for removal).",
    DeprecationWarning,
    stacklevel=2,
)
