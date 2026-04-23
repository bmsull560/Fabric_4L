/**
 * Canonical agent result envelope types for Fabric 4L frontend.
 *
 * All agent API responses conform to this shape.
 */

export interface AgentErrorDetail {
  code: string;
  message: string;
  node_id?: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}

export interface AgentResultMetadata {
  trace_id: string;
  workflow_id: string;
  tenant_id: string;
  agent_type: string;
  started_at: string; // ISO 8601
  completed_at: string; // ISO 8601
  duration_ms: number;
  node_path: string[];
}

export interface AgentResultEnvelope {
  status: "success" | "error" | "paused";
  data: Record<string, unknown> | null;
  error: AgentErrorDetail | null;
  metadata: AgentResultMetadata;
}
