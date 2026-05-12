"""Decision store stub — restores the import surface needed by benchmark_router.py.

The full implementation was removed from the repo in an earlier refactor.
This stub exists only so the benchmark script remains importable and
syntax-checkable until a proper Layer 1 source tree is restored.
"""

from __future__ import annotations


class InMemoryCrawlDecisionRepository:
    """Minimal stub for the in-memory decision repository."""
    pass
