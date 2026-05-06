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
