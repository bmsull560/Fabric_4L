# Auth/Tenant TODO-FIXME Audit (2026-05-12)

## Classification

| Source | Item | Classification | Disposition |
|---|---|---|---|
| `docs/operations/tenant-management-phase-2-provisioning.md` | Webhook idempotency follow-up for `X-Webhook-ID` persistence verification. | pending-with-ticket | Tracked as **SEC-4271**. Owner: **Platform Identity**. Target milestone: **M4-2026Q3**. |
| `docs/gate-alignment/implementation-plan-phases-1-3.md` | Redis-backed audit ledger chain-head persistence (`GET`/`SET`) placeholders. | pending-with-ticket | Replaced inline TODOs with **SEC-4312**. Owner: **Platform Security**. Target milestone: **M4-2026Q3**. |
| `docs/gate-alignment/implementation-plan-phases-1-3.md` | Retrieval-time ACL enforcement gap in phase 3.2 narrative. | pending-with-ticket | Replaced inline TODO with **SEC-4318**. Owner: **Layer 4 Agents**. Target milestone: **M1-2027Q1**. |
| `config/production-readiness/l3-tenant-isolation-gate.yaml` | Historical phase-0 marker references under a closed gate. | implemented-and-needs-doc-update | Normalized phrasing to historical “temporary phase-0 security markers” and removed stale TODO terminology from active gate config. |
| `config/production-readiness/l3-tenant-isolation-gate.yaml` | Closed gate still carried obsolete “pending phase” language in module notes. | obsolete | Removed stale pending wording and aligned module/gate status text to closed/complete state. |

## Notes

- Sweep scope: `docs/governance/`, `docs/operations/`, `docs/gate-alignment/`, `docs/launch/`, `docs/audit/`, and `config/production-readiness/`.
- Production-readiness gate config now references only active or historical-complete items (no unresolved security TODO markers).
- CI policy now blocks unresolved security-critical auth/tenant TODO/FIXME markers in release-scoped paths.
