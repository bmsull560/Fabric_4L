"""Coreference resolution package for entity deduplication."""

from .coreference_resolver import (
    CoreferenceCluster,
    CoreferenceResolver,
    CoreferenceRule,
    ResolutionMethod,
)

__all__ = [
    "CoreferenceResolver",
    "CoreferenceCluster",
    "CoreferenceRule",
    "ResolutionMethod",
]
