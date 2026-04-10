"""Coreference resolution package for entity deduplication."""

from .coreference_resolver import (
    CoreferenceResolver,
    CoreferenceCluster,
    CoreferenceRule,
    ResolutionMethod,
)

__all__ = [
    "CoreferenceResolver",
    "CoreferenceCluster",
    "CoreferenceRule",
    "ResolutionMethod",
]
