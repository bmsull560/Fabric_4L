"""Compatibility shim; expose the canonical Layer 6 API module object."""

import sys

from value_fabric.layer6.api import main as _canonical_main

sys.modules[__name__] = _canonical_main
