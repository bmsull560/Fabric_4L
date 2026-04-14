"""Tests for error handling exceptions, models, handlers and middleware."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    ValueFabricException,
)
from ..handlers import (
    _sanitize_trace_id,
    get_request_trace_id,
    global_exception_handler,
    http_exception_handler,
    is_production,
    register_exception_handlers,
    sanitize_error_details,
    validation_exception_handler,
    value_fabric_exception_handler,
)
from ..middleware import MAX_REQUEST_ID_LENGTH, RequestIDMiddleware, get_request_id
from ..models import ErrorCode, ErrorResponse


# ═══════════════════════════════════════════════════════════════════════════
# Exception classes
# ═══════════════════════════════════════════════════════════════════════════


class TestValueFabricException:
    def test_default_attributes(self):
        exc = ValueFabricException("something broke")
        assert exc.message == "something broke"
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500
        assert exc.details == {}

    def test_custom_attributes(self):
        exc = ValueFabricException(
            "bad input",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details={"field": "name"},
        )
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 422
        assert exc.details == {"field": "name"}

    def test_to_dict_with_details(self):
        exc = ValueFabricException("err", details={"key": "val"})
        d = exc.to_dict(include_details=True)
        assert d["message"] == "err"
        assert d["details"] == {"key": "val"}

    def test_to_dict_without_details(self):
        exc = ValueFabricException("err", details={"key": "val"})
        d = exc.to_dict(include_details=False)
        assert "details" not in d


class TestExceptionSubclasses:
    def test_authentication_error(self):
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.AUTHENTICATION_ERROR

    def test_authorization_error(self):
        exc = AuthorizationError()
        assert exc.status_code == 403
        assert exc.error_code == ErrorCode.AUTHORIZATION_ERROR

    def test_not_found_error_default(self):
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.message == "Resource not found"

    def test_not_found_error_with_id(self):
        exc = NotFoundError(resource_type="User", resource_id="42")
        assert "42" in exc.message
        assert exc.details["resource_id"] == "42"
        assert exc.details["resource_type"] == "User"

    def test_not_found_error_custom_message(self):
        exc = NotFoundError(message="custom not found")
        assert exc.message == "custom not found"

    def test_validation_error(self):
        exc = ValidationError(field="email")
        assert exc.status_code == 422
        assert exc.details["field"] == "email"

    def test_rate_limit_error(self):
        exc = RateLimitError(retry_after=60)
        assert exc.status_code == 429
        assert exc.details["retry_after_seconds"] == 60

    def test_service_unavailable_error(self):
        exc = ServiceUnavailableError(service="Neo4j")
        assert exc.status_code == 503
        assert exc.details["service"] == "Neo4j"


# ═══════════════════════════════════════════════════════════════════════════
# ErrorCode / ErrorResponse models
# ═══════════════════════════════════════════════════════════════════════════


class TestErrorCode:
    def test_is_string_enum(self):
        assert isinstance(ErrorCode.NOT_FOUND, str)
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"

    def test_all_codes_unique(self):
        values = [e.value for e in ErrorCode]
        assert len(values) == len(set(values))


class TestErrorResponse:
    def test_creation(self):
        resp = ErrorResponse(
            code=ErrorCode.NOT_FOUND,
            message="Not found",
            trace_id="req_abc",
        )
        assert resp.code == ErrorCode.NOT_FOUND
        assert resp.message == "Not found"
        assert resp.trace_id == "req_abc"
        assert resp.details is None

    def test_json_serialization(self):
        resp = ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message="Oops",
            trace_id="req_xyz",
            details={"info": "test"},
        )
        d = resp.model_dump()
        assert d["code"] == "INTERNAL_ERROR"
        assert d["details"] == {"info": "test"}


# ═══════════════════════════════════════════════════════════════════════════
# Handlers
# ═══════════════════════════════════════════════════════════════════════════


class TestIsProduction:
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_production(self):
        assert is_production() is True

    @patch.dict(os.environ, {"ENVIRONMENT": "staging"})
    def test_staging(self):
        assert is_production() is True

    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    def test_development(self):
        assert is_production() is False

    @patch.dict(os.environ, {}, clear=True)
    def test_default_not_production(self):
        os.environ.pop("ENVIRONMENT", None)
        os.environ.pop("ENV", None)
        os.environ.pop("APP_ENV", None)
        assert is_production() is False


class TestSanitizeErrorDetails:
    def test_none_input(self):
        assert sanitize_error_details(None) is None

    def test_removes_sensitive_keys(self):
        details = {"password": "secret", "user": "alice"}
        result = sanitize_error_details(details)
        assert "password" not in result
        assert result["user"] == "alice"

    def test_removes_key_with_sensitive_substring(self):
        details = {"auth_token": "xyz", "display_name": "Bob"}
        result = sanitize_error_details(details)
        assert "auth_token" not in result
        assert result["display_name"] == "Bob"

    def test_truncates_long_values(self):
        details = {"message": "x" * 2000}
        result = sanitize_error_details(details)
        assert len(result["message"]) < 2000
        assert result["message"].endswith("... [truncated]")

    def test_returns_none_for_empty_after_sanitize(self):
        details = {"password": "secret", "token": "xyz"}
        result = sanitize_error_details(details)
        assert result is None


class TestSanitizeTraceId:
    def test_valid_id_passes_through(self):
        assert _sanitize_trace_id("req_abc123") == "req_abc123"

    def test_strips_invalid_characters(self):
        result = _sanitize_trace_id("req<script>alert(1)</script>")
        assert "<" not in result
        assert ">" not in result

    def test_truncates_long_id(self):
        long_id = "a" * 100
        result = _sanitize_trace_id(long_id)
        assert len(result) <= 64

    def test_empty_generates_new(self):
        result = _sanitize_trace_id("")
        assert result.startswith("req_")


# ═══════════════════════════════════════════════════════════════════════════
# Middleware
# ═══════════════════════════════════════════════════════════════════════════


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware using FastAPI TestClient."""

    def _make_app(self, **kwargs) -> FastAPI:
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware, **kwargs)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"trace_id": getattr(request.state, "trace_id", None)}

        return app

    def test_generates_request_id_when_missing(self):
        client = TestClient(self._make_app())
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert resp.headers["X-Request-ID"].startswith("req_")

    def test_preserves_valid_request_id(self):
        client = TestClient(self._make_app())
        resp = client.get("/test", headers={"X-Request-ID": "my-custom-id"})
        assert resp.headers["X-Request-ID"] == "my-custom-id"

    def test_rejects_invalid_characters(self):
        client = TestClient(self._make_app())
        resp = client.get("/test", headers={"X-Request-ID": "<script>"})
        # Should generate a new ID instead
        assert "<" not in resp.headers["X-Request-ID"]
        assert resp.headers["X-Request-ID"].startswith("req_")

    def test_truncates_long_id(self):
        client = TestClient(self._make_app())
        long_id = "a" * 200
        resp = client.get("/test", headers={"X-Request-ID": long_id})
        assert len(resp.headers["X-Request-ID"]) <= MAX_REQUEST_ID_LENGTH

    def test_custom_generator(self):
        client = TestClient(self._make_app(generator=lambda: "custom-id"))
        resp = client.get("/test")
        assert resp.headers["X-Request-ID"] == "custom-id"


class TestGetRequestId:
    def test_from_state(self):
        request = MagicMock()
        request.state.trace_id = "from-state"
        assert get_request_id(request) == "from-state"

    def test_from_header_fallback(self):
        request = MagicMock()
        request.state = MagicMock(spec=[])  # no trace_id attribute
        request.headers = {"X-Request-ID": "from-header"}
        assert get_request_id(request) == "from-header"

    def test_unknown_fallback(self):
        request = MagicMock()
        request.state = MagicMock(spec=[])
        request.headers = {}
        assert get_request_id(request) == "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# Integration: exception handlers registered on a real FastAPI app
# ═══════════════════════════════════════════════════════════════════════════


class TestRegisteredHandlers:
    """End-to-end tests using the full handler registration."""

    @pytest.fixture
    def app(self):
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        register_exception_handlers(app)

        @app.get("/vf-error")
        async def vf_error():
            raise NotFoundError(resource_type="Widget", resource_id="99")

        @app.get("/http-error")
        async def http_error():
            raise HTTPException(status_code=403, detail="Forbidden")

        @app.get("/unhandled")
        async def unhandled():
            raise RuntimeError("boom")

        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app, raise_server_exceptions=False)

    def test_vf_exception_handler(self, client):
        resp = client.get("/vf-error")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "NOT_FOUND"
        assert "Widget" in body["message"]
        assert "X-Request-ID" in resp.headers

    def test_http_exception_handler(self, client):
        resp = client.get("/http-error")
        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == "AUTHORIZATION_ERROR"

    def test_global_exception_handler(self, client):
        resp = client.get("/unhandled")
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == "INTERNAL_ERROR"
