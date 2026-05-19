"""Layer 3 v2 bounded routers.

These modules are the freeze-safe, domain-driven replacements for the
routes registered directly on app_monolith.py.  New endpoints must be
added here, not to app_monolith.py (enforced by CI: check_l3_monolith_freeze.py).
"""
