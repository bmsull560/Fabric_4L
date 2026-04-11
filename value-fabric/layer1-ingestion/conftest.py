"""Pytest configuration for Layer 1 Ingestion tests."""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports (at the very beginning)
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Ensure PYTHONPATH includes src for subprocesses
os.environ["PYTHONPATH"] = src_path + os.pathsep + os.environ.get("PYTHONPATH", "")
