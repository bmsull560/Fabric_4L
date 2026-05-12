"""Layer 3 version compatibility wiring."""

from __future__ import annotations

from typing import Any

from .versioning import (
    initialize_versioning,
    migrate_v1_to_v2_ingestion_request,
    migrate_v1_to_v2_search_request,
    transform_v1_health_response,
    transform_v1_search_response,
)


def initialize_version_compatibility(register_handler) -> Any:
    vc = initialize_versioning("v1")
    register_handler(vc, from_version="v1", to_version="v2", handler=migrate_v1_to_v2_search_request, required=True)
    register_handler(vc, from_version="v1", to_version="v2", handler=migrate_v1_to_v2_ingestion_request, required=True)
    vc.register_response_transformer("v1", "/v1/search", transform_v1_search_response)
    vc.register_response_transformer("v1", "/health", transform_v1_health_response)
    return vc
