# WorkflowStalled Runbook

## Severity: warning

## Alert Condition
`increase(layer4_workflow_executions_total{status="running"}[30m]) == 0 and layer4_workflow_executions_total{status="running"} > 0` for 5 minutes.

## Impact
Long-running workflows are blocked. Background jobs and user requests may time out.

## Triage Steps
1. List running workflows via the Layer 4 API or database.
2. Check agent logs for errors, retries, or deadlocks.
3. Verify external dependencies (Neo4j, Redis, LLM APIs) are healthy.

## Resolution
### Quick Fix
- Cancel or restart the stuck workflow if it is safe to do so.
- Re-queue the workflow after fixing the dependency issue.
- Scale the agent executor pool if queue depth is high.

### Root Cause Analysis
- Inspect the workflow state graph for loops or blocked nodes.
- Review checkpoint/save logic for database locks.

## Escalation
- Page the platform on-call if multiple workflows are stalled.
- Contact `#vf-platform-oncall`.

## Prevention
- Add workflow-level timeouts and heartbeat checks.
- Improve idempotency so workflows can resume safely.
- Monitor workflow step completion rates.
