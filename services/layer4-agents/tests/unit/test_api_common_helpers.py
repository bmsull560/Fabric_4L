from fastapi import HTTPException

from src.api.common.errors import normalize_exception


def test_normalize_exception_passthrough_http_exception() -> None:
    original = HTTPException(status_code=422, detail="account_id is required for smoke-mode ROI validation")

    normalized = normalize_exception(
        original,
        status_code=500,
        detail="unused",
    )

    assert normalized is original
    assert normalized.status_code == 422
    assert normalized.detail == "account_id is required for smoke-mode ROI validation"


def test_normalize_exception_wraps_non_http_exception() -> None:
    normalized = normalize_exception(
        RuntimeError("boom"),
        status_code=500,
        detail="ROI analysis failed: boom",
    )

    assert isinstance(normalized, HTTPException)
    assert normalized.status_code == 500
    assert normalized.detail == "ROI analysis failed: boom"
