# Fifth Three-Sprint Live-Readiness Plan

This plan records one additional bounded live-readiness loop after the fourth loop established CI-callable artifact schema validation. The prior marginal-value assessment remains valid: a full live stack run is the next confidence-changing activity. This fifth loop was justified only because three concrete, non-speculative hardening tasks remained around evidence safety, maintainer installation, and explicit no-more-loop criteria.

| Sprint | Highest-priority target | Implementation intent | Material value |
|---|---|---|---|
| Sprint 10 | Evidence redaction and secret-pattern enforcement | Extend the artifact validator so live evidence bundles can be rejected when they contain obvious secret material. | Prevents unsafe artifact publication and makes the live gate safer to use in CI or review workflows. |
| Sprint 11 | Maintainer workflow installation guard | Add a deterministic installer/checker for the documented GitHub Actions workflow template without requiring this automation identity to modify protected workflow paths. | Gives maintainers a safe, auditable path to install the workflow that was blocked by repository permission rules. |
| Sprint 12 | Stop-decision evidence and runbook closure | Document the fifth-loop status and explicit criteria for when additional loops become nominal unless a live run exposes new failures. | Keeps future work focused on real live execution rather than speculative guardrail churn. |

## Implementation Status

| Sprint | Status | Implemented artifact | Validation target |
|---|---|---|---|
| Sprint 10 | Complete | `scripts/ci/validate_live_workflow_artifacts.py` now includes high-confidence secret-pattern scanning for text artifacts and a `--skip-secret-scan` escape hatch for emergency diagnostics. | Artifact bundles should fail schema validation when obvious API keys, provider tokens, private key blocks, or bearer-token assignments are present. |
| Sprint 11 | Complete | `scripts/ci/install_live_workflow_template.py` installs or checks the reviewed workflow template at `.github/workflows/live-workflow-validation.yml` for maintainers with workflow-write permission. | Maintainers can run `python scripts/ci/install_live_workflow_template.py --check` to verify exact parity before or after installation. |
| Sprint 12 | Complete | This plan and `docs/validation/live-workflow-validation.md` now record the fifth-loop closure criteria and proper-environment readiness status. | The repository does not claim live success until the live stack, seed, and Playwright workflow execute with mocks disabled. |

## Stop Criterion After Sprint 12

Additional autonomous hardening loops should stop unless a proper live environment exposes a new concrete failure or enables a previously blocked end-to-end validation step. At this point, further local sandbox live debugging is intentionally out of scope because the code path is prepared for a properly provisioned live environment, while the decisive evidence still has to come from a real live stack run with deterministic seed and browser validation enabled.

## Acceptance Criteria

The loop is complete when the new validator and installer scripts pass syntax checks, the config-only live gate still emits schema-valid artifacts, documentation is updated, and the repository is pushed to `origin/main`. The result must not claim live workflow success unless the live stack, seed, and browser workflow validation are executed with mocks disabled.
