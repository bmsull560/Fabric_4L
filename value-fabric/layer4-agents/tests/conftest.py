"""Pytest configuration for Layer 4 Agents tests.

Adds the layer4-agents directory to PYTHONPATH for proper import resolution.
This allows imports like 'from src.workflows.base import ...' to work correctly
with the relative imports within the src package.
"""

import sys
import os

# Calculate absolute path to layer4-agents directory (parent of tests)
# This allows 'src' to be imported as a package
tests_dir = os.path.dirname(os.path.abspath(__file__))
layer4_dir = os.path.dirname(tests_dir)
value_fabric_dir = os.path.dirname(layer4_dir)  # Parent of layer4-agents

if layer4_dir not in sys.path:
    sys.path.insert(0, layer4_dir)
if value_fabric_dir not in sys.path:
    sys.path.insert(0, value_fabric_dir)
