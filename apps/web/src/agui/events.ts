/**
 * AG-UI Protocol — Event Type Definitions
 *
 * Implements the Agent–User Interaction (AG-UI) Protocol event taxonomy.
 * Reference: https://docs.ag-ui.com/concepts/events
 *
 * These types define the canonical event shapes that flow between the agent
 * backend and the frontend. The transport layer (SSE, WebSocket, polling)
 * is abstracted away — these types describe *what* happened, not *how*
 * it was delivered.
 *
 * UI Contract (Data):
 *   Every event has a `type` discriminant, a `timestamp`, and an optional
 *   `runId` for correlation. Payload shapes are event-specific.
 *
 * UI Contract (Behavior):
 *   Events are ordered and idempotent. Replaying the same event sequence
 *   must produce the same UI state. Missing events degrade gracefully
 *   (e.g. a STEP_FINISHED without a preceding STEP_STARTED is ignored).
 */

// ── Event Type Enum ─────────────────────────────────────────────────────────

export enum AgentEventType {
  // Lifecycle events
  RUN_STARTED = "RUN_STARTED",
  RUN_FINISHED = "RUN_FINISHED",
  RUN_ERROR = "RUN_ERROR",

  // Step events (agent processing phases)
  STEP_STARTED = "STEP_STARTED",
  STEP_FINISHED = "STEP_FINISHED",

  // Text message events (streaming content)
  TEXT_MESSAGE_START = "TEXT_MESSAGE_START",
  TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT",
  TEXT_MESSAGE_END = "TEXT_MESSAGE_END",

  // Tool call events (agent invoking capabilities)
  TOOL_CALL_START = "TOOL_CALL_START",
  TOOL_CALL_END = "TOOL_CALL_END",

  // State events
  STATE_DELTA = "STATE_DELTA",
  STATE_SNAPSHOT = "STATE_SNAPSHOT",

  // Custom events (domain-specific extensions)
  CUSTOM = "CUSTOM",
}

// ── Step Status ─────────────────────────────────────────────────────────────

export type StepStatus = "pending" | "active" | "done" | "error" | "skipped";

// ── Base Event ──────────────────────────────────────────────────────────────

export interface BaseAgentEvent {
  /** Discriminant — determines the payload shape */
  type: AgentEventType;
  /** ISO-8601 timestamp of when the event was produced */
  timestamp: string;
  /** Correlation ID for the current agent run */
  runId?: string;
  /** Optional raw event ID for deduplication */
  eventId?: string;
}

// ── Lifecycle Events ────────────────────────────────────────────────────────

export interface RunStartedEvent extends BaseAgentEvent {
  type: AgentEventType.RUN_STARTED;
  /** Human-readable run description */
  description?: string;
  /** Expected steps (if known upfront) */
  expectedSteps?: Array<{ id: string; label: string }>;
  /** Metadata from the backend (trace, tenant, workflow IDs) */
  metadata?: RunMetadata;
}

export interface RunFinishedEvent extends BaseAgentEvent {
  type: AgentEventType.RUN_FINISHED;
  /** Final output / summary */
  output?: unknown;
  metadata?: RunMetadata;
}

export interface RunErrorEvent extends BaseAgentEvent {
  type: AgentEventType.RUN_ERROR;
  /** Error message */
  message: string;
  /** Error code (HTTP status or domain code) */
  code?: string;
  /** Whether the run can be retried */
  retryable?: boolean;
}

// ── Step Events ─────────────────────────────────────────────────────────────

export interface StepStartedEvent extends BaseAgentEvent {
  type: AgentEventType.STEP_STARTED;
  /** Unique step identifier within the run */
  stepId: string;
  /** Human-readable step label */
  label: string;
  /** Step index (0-based) */
  index?: number;
}

export interface StepFinishedEvent extends BaseAgentEvent {
  type: AgentEventType.STEP_FINISHED;
  /** Step identifier (must match a preceding STEP_STARTED) */
  stepId: string;
  /** Outcome of the step */
  status: "done" | "error" | "skipped";
  /** Optional result data */
  result?: unknown;
}

// ── Text Message Events ─────────────────────────────────────────────────────

export interface TextMessageStartEvent extends BaseAgentEvent {
  type: AgentEventType.TEXT_MESSAGE_START;
  /** Message identifier for correlating content chunks */
  messageId: string;
  /** Role of the message author */
  role: "agent" | "system";
}

export interface TextMessageContentEvent extends BaseAgentEvent {
  type: AgentEventType.TEXT_MESSAGE_CONTENT;
  /** Message identifier */
  messageId: string;
  /** Incremental text content (append to previous) */
  delta: string;
}

export interface TextMessageEndEvent extends BaseAgentEvent {
  type: AgentEventType.TEXT_MESSAGE_END;
  /** Message identifier */
  messageId: string;
}

// ── Tool Call Events ────────────────────────────────────────────────────────

export interface ToolCallStartEvent extends BaseAgentEvent {
  type: AgentEventType.TOOL_CALL_START;
  /** Tool call identifier */
  toolCallId: string;
  /** Name of the tool being invoked */
  toolName: string;
  /** Arguments passed to the tool */
  args?: Record<string, unknown>;
}

export interface ToolCallEndEvent extends BaseAgentEvent {
  type: AgentEventType.TOOL_CALL_END;
  /** Tool call identifier */
  toolCallId: string;
  /** Tool execution result */
  result?: unknown;
  /** Whether the tool call succeeded */
  success: boolean;
  /** Error message if failed */
  error?: string;
}

export interface PageActionPayload {
  entityType: "signal" | "evidence" | "hypothesis" | "scenario";
  entityId: string;
  accountId: string;
  caseId: string;
  tenantId?: string;
  intendedOperation: "signal_review" | "evidence_attach" | "hypothesis_convert" | "scenario_update";
  payload?: Record<string, unknown>;
  runMetadataIds?: {
    runId: string;
    traceId: string;
    workflowId?: string;
    auditEventId: string;
    toolCallId?: string;
  };
}

// ── State Events ────────────────────────────────────────────────────────────

export interface StateDeltaEvent extends BaseAgentEvent {
  type: AgentEventType.STATE_DELTA;
  /** JSON Merge Patch (RFC 7396) to apply to the current state */
  delta: Record<string, unknown>;
}

export interface StateSnapshotEvent extends BaseAgentEvent {
  type: AgentEventType.STATE_SNAPSHOT;
  /** Complete state snapshot (replaces current state) */
  snapshot: Record<string, unknown>;
}

// ── Custom Events ───────────────────────────────────────────────────────────

export interface CustomEvent extends BaseAgentEvent {
  type: AgentEventType.CUSTOM;
  /** Domain-specific event name */
  name: string;
  /** Arbitrary payload */
  payload?: unknown;
}

// ── Union Type ──────────────────────────────────────────────────────────────

export type AgentEvent =
  | RunStartedEvent
  | RunFinishedEvent
  | RunErrorEvent
  | StepStartedEvent
  | StepFinishedEvent
  | TextMessageStartEvent
  | TextMessageContentEvent
  | TextMessageEndEvent
  | ToolCallStartEvent
  | ToolCallEndEvent
  | StateDeltaEvent
  | StateSnapshotEvent
  | CustomEvent;

// ── Run Metadata ────────────────────────────────────────────────────────────

export type SemanticContractMode = "warn" | "strict";
export type SemanticContractSeverity = "warning" | "error";

export interface SemanticContractViolation {
  code: string;
  message: string;
  severity: SemanticContractSeverity;
  path: string;
}

export interface SemanticContractVersions {
  semanticContract?: string;
  agentRegistry?: string;
  prompt?: string;
  tool?: string;
  workflow?: string;
  memory?: string;
  [key: string]: string | undefined;
}

export interface SemanticProvenance {
  tenantId?: string;
  traceId?: string;
  workflowId?: string;
  auditEventId?: string;
  sourceNode?: string;
  sourceLayer?: string;
  [key: string]: string | undefined;
}

export interface RunMetadata {
  runId?: string;
  traceId?: string;
  workflowId?: string;
  tenantId?: string;
  auditEventId?: string;
  /** Workflow node that produced this event */
  sourceNode?: string;
  intent?: string;
  confidence?: number;
  semanticContractVersion?: string;
  semanticContractValid?: boolean;
  semanticContractMode?: SemanticContractMode;
  semanticContractViolations?: SemanticContractViolation[];
  contractVersions?: SemanticContractVersions;
  provenance?: SemanticProvenance;
  [key: string]: unknown;
}

// ── Step Snapshot (derived state for UI rendering) ──────────────────────────

export interface StepSnapshot {
  id: string;
  label: string;
  status: StepStatus;
  startedAt?: string;
  finishedAt?: string;
  result?: unknown;
}
