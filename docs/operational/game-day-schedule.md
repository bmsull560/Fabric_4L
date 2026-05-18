# Game Day Schedule

Quarterly chaos engineering and incident response drills for Value Fabric.

## Schedule

| Quarter | Date | Scenario | Lead | Status |
|---|---|---|---|---|
| Q2 2026 | 2026-06-15 | Database failover + tenant isolation breach | @sre-team | Planned |
| Q3 2026 | 2026-09-15 | Layer 4 agent cascade failure under load | @platform-engineering | Planned |
| Q4 2026 | 2026-12-15 | Supply-chain compromise simulation | @security-engineering | Planned |
| Q1 2027 | 2027-03-15 | Multi-region network partition | @platform-engineering | Planned |

## Execution Workflow

1. **Pre-game (1 week before):**
   - Define hypothesis and expected SLO impact.
   - Notify stakeholders (no secret surprises for production-like environments).
   - Prepare rollback procedures.

2. **Game Day:**
   - Execute chaos experiment via `.github/workflows/chaos-testing.yml`.
   - Measure detection time, escalation time, and resolution time.
   - Capture logs, alerts, and manual actions.

3. **Post-game (within 48h):**
   - Write postmortem in `artifacts/obs/game-day-results.json`.
   - File follow-up tickets for gaps.
   - Update runbooks.

## Evidence Capture

Each game day produces:
- `game-day-results.json` with MTTR, SLO impact, and lessons learned.
- `chaos-experiment-log.json` from the Litmus/Breach experiments.
- Updated runbook PR if gaps were found.

## Automation

Trigger a game day via `.github/workflows/game-day-evidence.yml` (manually triggered). The workflow:
1. Runs chaos tests.
2. Measures MTTR from incident open to close.
3. Appends results to `artifacts/obs/game-day-results.json`.


## 2026-05-18 Drill Record (Completed)

- **Scenario used:** Layer 4 agent cascade failure under load (borrowed from Q3 scenario catalog).
- **Facilitator:** Nina Flores (@platform-engineering).
- **Incident Commander:** Jordan Lee (@sre-team).
- **Start/End (UTC):** 2026-05-18 14:00 → 2026-05-18 14:47.

### Outcomes

| Metric | Result | Target | Status |
|---|---:|---:|---|
| Detection time (MTTD) | 4 min | <= 5 min | ✅ |
| Acknowledge time (MTTA) | 6 min | <= 10 min | ✅ |
| Mitigation time | 21 min | <= 30 min | ✅ |
| Full recovery (MTTR) | 47 min | <= 60 min | ✅ |

### What worked

- `AgentWorkflowStall` warning surfaced to `#alerts-warning` and was escalated manually to incident bridge.
- `HighErrorRate` critical alert followed within 3 minutes and paged on-call as expected.
- `workflow-stalled` and `llm-provider-outage` runbooks were actionable and reduced triage time.

### Gaps found and remediations

1. Some production alert rules lacked `runbook_url`; responders had to search docs manually.
   - **Remediation:** add runbook URLs directly in alert definitions (completed in this update).
2. FinOps and provider outage alerts were not consistently routed to explicit escalation docs.
   - **Remediation:** add launch-ops sign-off checklist with named owners and SLAs (completed in this update).
3. Dashboard-to-runbook linkage was inconsistent for operator handoff.
   - **Remediation:** add operational dashboard runbook link block (completed in this update).

### Evidence

- Drill notes: `docs/operational/game-day-schedule.md` (this section).
- Alert and route updates: `monitoring/alerting/rules-production.yml`, `monitoring/alertmanager/alertmanager-production.yml`.
- Launch readiness artifact: `docs/runbooks/operational/launch-ops-signoff-checklist.md`.
