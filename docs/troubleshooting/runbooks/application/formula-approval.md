# Formula Approval Runbook

> Policy reference: [Incident Severity Matrix and On-Call Escalation Policy](../operations/severity-escalation-policy.md).


## Severity: warning

## Alert Condition
`layer4_formula_approval_pending > 0` for more than 1 minute.

## Impact
Pending formula approvals block activation of new or updated formulas. Downstream workflows that depend on the formula may be delayed.

## Triage Steps
1. Check the Layer 4 Agents metrics endpoint (`/metrics`) for `layer4_formula_approval_pending{tenant_id="..."}`.
2. Identify the tenant and the specific formulas awaiting approval via the Layer 4 API or Neo4j Browser.
3. Review the formula changes, dependencies, and validation results in the governance UI or API.

## Resolution
### Quick Fix
- If the formula is valid and safe, call `POST /v1/formulas/{id}/approve` (or equivalent governance API) to approve it.
- If the formula is incorrect or risky, call `POST /v1/formulas/{id}/reject` with a reason and request the submitter to revise.

### Root Cause Analysis
- Investigate why the approval queue grew: too many submissions, missing approvers, or automated pipeline failures.
- Ensure that approvers have the `tenant_admin` or `content_admin` role.

## Escalation
- If formulas are stuck due to a service error (e.g., Neo4j unavailability), escalate to the platform on-call.
- Contact: `#vf-platform-oncall` or page the SRE rotation.

## Prevention
- Implement automated governance checks to pre-validate formulas before submission.
- Set up a regular review cadence and ensure at least two approvers per tenant.
- Monitor the `layer4_formula_approval_pending` gauge and alert early.
