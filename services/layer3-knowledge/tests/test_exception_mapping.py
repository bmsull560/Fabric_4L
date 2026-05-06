from value_fabric.layer3_knowledge.src.api.exception_mapping import map_exception_to_http_error
from value_fabric.layer3_knowledge.src.api.exceptions import DatabaseError, SearchError, ValidationError


def test_validation_error_maps_to_422_with_context():
    exc = ValidationError("bad input")
    err = map_exception_to_http_error(exc, context={"tenant": "t1", "endpoint": "/v1/entities", "operation": "list"})
    assert err.status_code == 422
    assert err.detail["code"] == "VALIDATION_ERROR"
    assert err.detail["context"]["tenant"] == "t1"


def test_database_error_maps_to_503():
    exc = DatabaseError("db down")
    err = map_exception_to_http_error(exc, context={"tenant": "t1", "endpoint": "/v1/models", "operation": "read"})
    assert err.status_code == 503
    assert err.detail["code"] == "DEPENDENCY_UNAVAILABLE"


def test_search_error_maps_to_502():
    exc = SearchError("bad gateway")
    err = map_exception_to_http_error(exc, context={"tenant": "t1", "endpoint": "/v1/search", "operation": "search"})
    assert err.status_code == 502
    assert err.detail["code"] == "SEARCH_BACKEND_ERROR"
