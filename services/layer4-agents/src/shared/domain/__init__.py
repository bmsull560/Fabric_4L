"""Shared domain models for Layer 4 Agents."""
from __future__ import annotations

from .context import TenantContext, TenantContextError

__all__ = ["TenantContext", "TenantContextError"]
