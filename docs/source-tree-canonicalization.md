# Source Tree Canonicalization (Layers 5-6)

## Ownership

- **Layer 5 canonical runtime modules:** `value_fabric/layer5/**`
- **Layer 6 canonical runtime modules:** `value_fabric/layer6/**`
- **Service tree ownership:** `services/layer5-ground-truth/` and `services/layer6-benchmarks/` own deployment wiring (Dockerfiles, service config, tests, manifests), while mirrored runtime modules are compatibility shims only.

## Compatibility policy

- Legacy imports via `services/layer6-benchmarks/src/*` remain temporarily supported through thin re-export shims.
- New code should import canonical modules from `value_fabric.layer5` or `value_fabric.layer6` directly.

## CI drift guard

CI enforces shim-only compatibility files for selected layer 6 mirror paths via:

- `scripts/ci/check_layer56_shims.py`

This guard fails if local logic is reintroduced into shim files.
