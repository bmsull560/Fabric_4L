"""Pytest configuration for Layer 4 Agents tests.

Adds the src directory to PYTHONPATH for proper import resolution.
"""

import sys
import os

# Calculate absolute path to src directory
# This works regardless of where pytest is invoked from
tests_dir = os.path.dirname(os.path.abspath(__file__))
layer4_dir = os.path.dirname(tests_dir)
src_path = os.path.join(layer4_dir, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)
