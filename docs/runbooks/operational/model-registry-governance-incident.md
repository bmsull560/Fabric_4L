# Model Registry Governance Incident Runbook

This runbook covers incidents where an unapproved, deprecated, blocked, or incorrectly versioned model is selected by Fabric_4L runtime services. The safe default is to stop new traffic to the affected model and roll back to the last approved production version.

## Severity Classification

| Severity | Condition | Expected response |
|---|---|---|
| SEV-1 | A blocked or unapproved model serves production traffic, or model output creates material customer risk. | Freeze model promotion, disable affected runtime selection, roll back immediately, and page model steward. |
| SEV-2 | A model version mismatch, missing model card, or failed eval gate is discovered before broad production impact. | Pause promotion and require steward approval before traffic resumes. |
| SEV-3 | Registry metadata drift or stale deprecation metadata is detected without runtime impact. | Repair registry metadata and add validation coverage. |

## Immediate Checks

Determine which runtime service selected the model, which registry record was used, and whether the selected version was in an allowed lifecycle state. Capture sanitized evidence only; provider API keys, prompt secrets, and tenant data must not be copied into incident records.

| Check | Evidence | Pass criterion |
|---|---|---|
| Registry state | Model ID, immutable version, lifecycle state, owner, approver. | Production traffic uses only `production` state records. |
| Eval gate | Golden trace, benchmark, and safety evidence linked to the registry record. | Required gates passed before promotion. |
| Runtime selection | Service config or audit event showing registry lookup. | Free-form model override is not used in production. |
| Rollback target | Previous production registry record. | Target is approved, monitored, and available. |

## Remediation Procedure

Set the affected model registry record to `blocked` or remove it from production routing if supported by the service. Roll back to the previous approved production version and confirm the runtime no longer accepts environment-variable model overrides. Run the golden-trace eval suite and compare cost, latency, and correctness deltas before reopening promotion.

## Closure Evidence

The incident can close only after runtime traffic uses the approved rollback or fixed production version, audit records link the change to an approver, eval evidence is attached, deprecation or block state is enforced, and the post-incident review identifies a prevention control such as stronger CI validation or runtime registry enforcement.
