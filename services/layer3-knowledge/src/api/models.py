"""Layer 3 compatibility shim for API models.

This module intentionally re-exports the canonical Layer 3 API models from
``value_fabric.layer3.api.models`` and must not contain service-local business
logic.
"""

from value_fabric.layer3.api.models import *  # noqa: F401,F403
