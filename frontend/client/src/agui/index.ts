/**
 * AG-UI Protocol — Agent–User Interaction Layer
 *
 * Implements the AG-UI protocol for standardized agent-frontend communication.
 * Reference: https://docs.ag-ui.com/introduction
 *
 * Architecture:
 *   events.ts           → Type definitions (event taxonomy)
 *   AgentEventClient.ts → Transport adapter (HTTP → AG-UI events)
 *   useAgentEvents.ts   → React hook (event stream → UI state)
 *
 * Usage:
 *   import { useAgentEvents, AgentEventType } from "@/agui";
 */

// ── Event Types ─────────────────────────────────────────────────────────────
export { AgentEventType } from "./events";
export type {
  AgentEvent,
  BaseAgentEvent,
  RunStartedEvent,
  RunFinishedEvent,
  RunErrorEvent,
  StepStartedEvent,
  StepFinishedEvent,
  TextMessageStartEvent,
  TextMessageContentEvent,
  TextMessageEndEvent,
  ToolCallStartEvent,
  ToolCallEndEvent,
  StateDeltaEvent,
  StateSnapshotEvent,
  CustomEvent,
  RunMetadata,
  StepSnapshot,
  StepStatus,
} from "./events";

// ── Transport ───────────────────────────────────────────────────────────────
export { sendAgentMessage, streamAgentEvents } from "./AgentEventClient";
export type { AgentEventClientOptions } from "./AgentEventClient";

// ── React Hook ──────────────────────────────────────────────────────────────
export { useAgentEvents } from "./useAgentEvents";
export type {
  RunState,
  UseAgentEventsOptions,
  UseAgentEventsReturn,
} from "./useAgentEvents";
