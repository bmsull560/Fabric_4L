# Layer 3 / Layer 6 canonical-vs-wrapper policy

## Purpose

`value_fabric/` is the canonical runtime source for Layer 3 and Layer 6 API modules.
Service-local API modules under:

- `services/layer3-knowledge/src/api/`
- `services/layer6-benchmarks/src/api/`

are compatibility wrappers only, so deployable service import paths remain stable.

## Rules

1. Put implementation changes in canonical modules under:
   - `value_fabric/layer3/api/`
   - `value_fabric/layer6/api/`
2. Keep service-local modules as thin re-exports (`from value_fabric... import *`).
3. Preserve public import surfaces (entrypoints like `api.main`, route modules, and exported symbols).
4. If any files are intentionally duplicated instead of wrapped, register them in `scripts/mirrored_files.json` and keep hashes aligned with `python scripts/check_mirrored_files.py`.

## CI / drift guard

Run:

```bash
python scripts/check_mirrored_files.py
```

The check fails when configured mirrored file pairs diverge.
