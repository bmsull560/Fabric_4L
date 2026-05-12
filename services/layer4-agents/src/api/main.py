"""Thin entrypoint for Layer 4 API."""

from __future__ import annotations

from .app_factory import create_app

app = create_app()
