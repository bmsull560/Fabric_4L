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

<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours

## Allowed wrapper-only deviations

Wrapper-only edits are allowed **only** for deploy-time bootstrap concerns that cannot live in canonical runtime modules. Current allowed categories are:

1. Service process entry wiring (for example package/module invocation glue specific to `services/layer6-benchmarks`).
2. Deployment metadata outside mirrored runtime files (container manifests, service-local launch scripts, Helm/K8s wiring).

For the mirrored Layer 6 runtime files under:

- `value_fabric/layer6/`
- `services/layer6-benchmarks/src/`

there are currently **no approved content deviations**. These files must remain byte-for-byte aligned via `scripts/mirrored_files.json` and `scripts/check_mirrored_files.py`.

If a future exception is required, document it in this file with:

- exact file path(s)
- rationale
- expected removal date or follow-up issue
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
## Audit artifacts

Layer 6 wrapper drift-audit evidence lives in:

- `docs/contracts/layer6-audit-artifacts/`

Start with:

- `docs/contracts/layer6-audit-artifacts/README.md`
- `docs/contracts/layer6-audit-artifacts/active-milestones.md`

For every active milestone, keep both `report.md` and `checklist.md` under `milestones/<milestone-id>/`.

<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======


See also: `docs/reference/layer6-drift-audit-artifact-index.md` for current audit evidence and milestone artifact requirements.
>>>>>>> theirs
