"""Pytest configuration for Layer 1 Ingestion tests."""

import os
import sys
from pathlib import Path

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
