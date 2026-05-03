"""Compatibility namespace for legacy Layer 1 test imports.

The service now exposes canonical modules through ``value_fabric.layer1`` and
service-local packages, but older tests still import
``value_fabric.layer1_ingestion.src.*``.  Keep this as a source-checkout-only
namespace bridge so repository-level pytest collection is deterministic instead
of relying on ad hoc ``sys.path`` ordering.
"""

from __future__ import annotations

__all__: list[str] = []
