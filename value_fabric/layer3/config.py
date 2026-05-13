"""Compatibility-only shim for ``value_fabric.layer3.config.settings``.

Canonical Layer 3 runtime settings live in ``value_fabric/layer3/config/settings.py``.
This module remains for backward-compatible imports.
"""

from value_fabric.layer3.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
