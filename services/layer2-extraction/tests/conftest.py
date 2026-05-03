"""Pytest bootstrap for Layer 2 extraction tests.

The Layer 2 test suite may use a lightweight ``openai`` stub because specific
unit tests bypass client construction and do not exercise the OpenAI SDK. The
repository package namespace, however, must never be stubbed: repository-level
collection imports Layer 3 and Layer 4 tests in the same interpreter, and a
``sys.modules['value_fabric']`` module stub turns the real package namespace
into a non-package. H-04 therefore makes the shared ``value_fabric`` imports a
mandatory collection-time dependency instead of masking them with stubs.
"""

from __future__ import annotations

import importlib
import sys
import types

# ---------------------------------------------------------------------------
# openai stub — AsyncOpenAI is instantiated in EntityDeduplicator.__init__,
# which is bypassed in unit tests, so a bare type stub is sufficient.
# ---------------------------------------------------------------------------
if "openai" not in sys.modules:
    _openai = types.ModuleType("openai")
    _openai.AsyncOpenAI = type("AsyncOpenAI", (), {})
    sys.modules["openai"] = _openai

# ---------------------------------------------------------------------------
# value_fabric.shared is a mandatory repository package. Import it for an
# actionable collection-time failure if the monorepo bootstrap is broken, but
# never inject a ModuleType stub for the package root.
# ---------------------------------------------------------------------------
try:
    _typed_dict_module = importlib.import_module("value_fabric.shared.models.typed_dict")
except ModuleNotFoundError as exc:  # pragma: no cover - fail-fast bootstrap path
    raise RuntimeError(
        "Layer 2 tests require the real value_fabric.shared package. "
        "Run pytest from the repository root or install tests/requirements-test.txt; "
        "do not stub value_fabric because it breaks repository-level collection."
    ) from exc

if not hasattr(_typed_dict_module, "TypedDictModel"):
    _typed_dict_module.TypedDictModel = type("TypedDictModel", (), {})
