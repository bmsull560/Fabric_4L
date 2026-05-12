"""API main module (re-exports from layer2_extraction)."""

import sys

# Transparent alias so tests patching this module affect the real implementation
sys.modules[__name__] = __import__("layer2_extraction.api.main", fromlist=["*"])
