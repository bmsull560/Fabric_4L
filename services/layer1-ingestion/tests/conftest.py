"""Pytest configuration for Layer 1 Ingestion tests."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Stub optional heavy deps before any imports that transitively require them
try:
    import opentelemetry  # noqa: F401
except ImportError:
    import types
    import importlib.util
    def _make_pkg(name):
        m = types.ModuleType(name)
        m.__path__ = []
        spec = importlib.util.spec_from_loader(name, loader=None)
        spec.submodule_search_locations = []
        m.__spec__ = spec
        sys.modules[name] = m
        return m
    _otel = _make_pkg("opentelemetry")
    _otel_sdk = _make_pkg("opentelemetry.sdk")
    _otel_sdk.resources = _make_pkg("opentelemetry.sdk.resources")
    _otel_sdk.resources.Resource = type("Resource", (), {})

try:
    import psycopg2  # noqa: F401
except ImportError:
    sys.modules["psycopg2"] = MagicMock()

# Add src directory to Python path for imports
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Add parent directory (value-fabric) so shared.* packages are importable
shared_root = str(Path(__file__).parent.parent.parent)
if shared_root not in sys.path:
    sys.path.insert(0, shared_root)

# Ensure PYTHONPATH includes src for subprocesses
os.environ["PYTHONPATH"] = src_path + os.pathsep + shared_root + os.pathsep + os.environ.get("PYTHONPATH", "")
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'

