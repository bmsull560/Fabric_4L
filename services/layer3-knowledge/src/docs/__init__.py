"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Documentation package initialization.
"""

from ..docs.api_documentation import (
    API_DOCUMENTATION,
    APIEndpoint,
    APIError,
    APIExample,
    APIGuide,
    APITutorial,
    get_documentation,
    get_endpoint_documentation,
    get_error_documentation,
    get_guide,
    get_tutorial,
)

__all__ = [
    "APIExample",
    "APITutorial",
    "APIError",
    "APIEndpoint",
    "APIGuide",
    "get_documentation",
    "get_endpoint_documentation",
    "get_error_documentation",
    "get_tutorial",
    "get_guide",
    "API_DOCUMENTATION",
]
