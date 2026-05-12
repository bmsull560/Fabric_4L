from value_fabric.shared.fastapi_framework import RouterMount, include_router_mounts

from .routes import (
    benchmarks,
    calculators,
    compat_aliases,
    competitive_intel,
    entities,
    evidence,
    formula_governance,
    formulas,
    models,
    products,
    provenance_audit,
    roi_calculator,
    system,
    value_packs,
    value_trees,
    variables,
)


def register_router_groups(app) -> None:
    include_router_mounts(
        app,
        [
            RouterMount(value_trees.router, prefix="/v1"),
            RouterMount(formulas.router, prefix="/v1"),
            RouterMount(value_packs.router, prefix="/v1"),
            RouterMount(formula_governance.router, prefix="/v1"),
            RouterMount(variables.router, prefix="/v1"),
            RouterMount(models.router, prefix="/v1"),
            RouterMount(entities.router, prefix="/v1"),
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
