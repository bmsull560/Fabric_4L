"""Shared dependencies for Layer 6 API."""

from fastapi import Query


def industry_filter(industry: str | None = Query(None, description="Filter by industry")) -> str | None:
    return industry


def segment_filter(segment: str | None = Query(None, description="Filter by segment")) -> str | None:
    return segment
