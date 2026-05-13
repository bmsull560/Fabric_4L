"""Compatibility wrapper for the Layer 1 crawler package.

Deprecated import path: ``src.crawler``.
Canonical import path: ``value_fabric.layer1.crawler``.

Keep this module as a thin re-export only until remaining callers migrate.
"""

from value_fabric.layer1.crawler import *  # noqa: F401,F403
