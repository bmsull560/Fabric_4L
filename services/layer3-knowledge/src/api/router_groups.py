"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Service-local implementation permitted by runtime path governance.

Router ownership model (ARCH-L3-007):
- v2 bounded routers (api/routers/) are the canonical home for new endpoints.
- app_monolith.py is FROZEN: CI rejects any new @app.<method> routes added there.
- Full monolith removal: ARCH-L3-011 (Sprint 3).
"""
from value_fabric.shared.fastapi_framework import RouterMount, include_router_mounts

from ..api.routers import entities_v2, value_packs_v2
from ..api.routes import (
    benchmarks,
    calculators,
    compat_aliases,
    competitive_intel,
    evidence,
    formula_governance,
    formulas,
    models,
    products,
    provenance_audit,
    roi_calculator,
    system,
    value_trees,
    variables,
)


def register_router_groups(app) -> None:
    include_router_mounts(
        app,
        [
            # --- v2 bounded routers (ARCH-L3-007) ----------------------------
            # These are the freeze-safe, domain-driven modules.  New entity and
            # value-pack endpoints must be added here, not to app_monolith.py.
            RouterMount(entities_v2.router, prefix="/v1"),
            RouterMount(value_packs_v2.router, prefix="/v1"),
            # --- Remaining canonical route modules ---------------------------
            RouterMount(value_trees.router, prefix="/v1"),
            RouterMount(formulas.router, prefix="/v1"),
            RouterMount(formula_governance.router, prefix="/v1"),
            RouterMount(variables.router, prefix="/v1"),
            RouterMount(models.router, prefix="/v1"),
            RouterMount(products.router, prefix="/v1"),
            RouterMount(provenance_audit.router),
            RouterMount(evidence.router, prefix="/v1"),
            RouterMount(competitive_intel.router, prefix="/v1"),
            RouterMount(roi_calculator.router, prefix="/v1"),
            RouterMount(benchmarks.router, prefix="/v1/roi"),
            RouterMount(calculators.router, prefix="/v1"),
            RouterMount(system.router),
            RouterMount(compat_aliases.router),
        ],
    )
