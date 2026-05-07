"""Shared error helpers for API routes."""

from fastapi import HTTPException


def normalize_exception(exc: Exception, *, status_code: int, detail: str) -> HTTPException:
    """Preserve existing HTTP errors and normalize all other exceptions."""
    if isinstance(exc, HTTPException):
        return exc
    return HTTPException(status_code=status_code, detail=detail)


def raise_normalized(exc: Exception, *, status_code: int, detail: str) -> None:
    """Raise a normalized HTTPException while preserving existing HTTP payloads."""
    raise normalize_exception(exc, status_code=status_code, detail=detail)
