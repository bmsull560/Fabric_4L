"""Stable compatibility module for Layer 4 database imports.

Security tests and shared tooling import ``value_fabric.layer4.database``.
This module intentionally re-exports the fail-safe facade so those imports
remain stable even when optional Layer 4 runtime dependencies are unavailable.
"""

from value_fabric.layer4.database_facade import *  # noqa: F401,F403
