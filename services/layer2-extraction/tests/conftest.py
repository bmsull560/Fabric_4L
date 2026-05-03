"""Shared test configuration for layer2-extraction.

Registers lightweight stubs for packages that are not installed in the test
environment (openai, value_fabric) before any test module is collected.
Using conftest.py ensures the stubs are in place regardless of collection
order, preventing session-wide sys.modules pollution from individual test
files.
"""

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
# value_fabric.shared stub — pulled in transitively via layer2_extraction.models
# ---------------------------------------------------------------------------
_vf_stubs = [
    "value_fabric",
    "value_fabric.shared",
    "value_fabric.shared.models",
    "value_fabric.shared.models.typed_dict",
]
for _name in _vf_stubs:
    if _name not in sys.modules:
        sys.modules[_name] = types.ModuleType(_name)

if not hasattr(sys.modules["value_fabric.shared.models.typed_dict"], "TypedDictModel"):
    sys.modules["value_fabric.shared.models.typed_dict"].TypedDictModel = type(
        "TypedDictModel", (), {}
    )
