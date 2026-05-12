"""Shared DB dependency helpers for API routes."""

from __future__ import annotations

from ...database import get_db_from_context

get_route_db = get_db_from_context
