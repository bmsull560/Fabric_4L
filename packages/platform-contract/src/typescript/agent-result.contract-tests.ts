import type { AgentResultEnvelope } from "@fabric/platform-contract/agent-result";

const envelope: AgentResultEnvelope = {
  status: "success",
  data: {},
  error: null,
  metadata: {
    trace_id: "trace-1",
    workflow_id: "workflow-1",
    tenant_id: "tenant-1",
    agent_type: "planner",
    started_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    duration_ms: 1,
    node_path: ["start"],
  },
};

void envelope;
