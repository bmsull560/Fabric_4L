"""Compatibility shim for legacy Layer 3 entity route imports.

Canonical implementation lives in ``value_fabric.layer3.api.routes.entities``.
"""

from value_fabric.layer3.api.routes.entities import router

__all__ = ["router"]
