"""API routes package."""

# pack_loader has no external dependencies and must always be importable.
# Other routes require neo4j, FastAPI, and agent dependencies — wrap in
# try/except so lightweight consumers (tests, CI) can import pack_loader
# without a full runtime environment.
from . import pack_loader  # Always available — no external deps

try:
    from . import (
        _utils,
        benchmarks,
        competitive_intel,
        evidence,
        formula_governance,
        formulas,
        products,
        roi_calculator,
        value_packs,
        value_trees,
        variables,
    )
    _ROUTES_AVAILABLE = True
except (ImportError, Exception):
    _ROUTES_AVAILABLE = False

__all__ = [
    "pack_loader",
    "_ROUTES_AVAILABLE",
    "value_trees",
    "formulas",
    "value_packs",
    "formula_governance",
    "variables",
    "benchmarks",
    "products",
    "evidence",
    "competitive_intel",
    "roi_calculator",
    "_utils",
]
