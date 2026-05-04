/**
 * AgentEventClient — Transport adapter that converts backend responses
 * into AG-UI protocol events.
 *
 * This client sits between the raw HTTP layer and the React hooks.
 * It handles two transport modes:
 *
 *   1. **Request/Response** — The current `/agent-stream/chat` endpoint
 *      returns a single JSON response. The client synthesizes a full
 *      AG-UI event sequence from it (RUN_STARTED → steps → TEXT → RUN_FINISHED).
 *
 *   2. **SSE Streaming** — Future endpoints that emit `data: {...}` lines.
 *      The client parses each line and yields typed AgentEvent objects.
 *
 * UI Contract (Behavior):
 *   - `send()` always yields a complete event sequence starting with
 *     RUN_STARTED and ending with RUN_FINISHED or RUN_ERROR.
 *   - Steps are synthesized from the `activeTab` context to show the
 *     user what the agent is doing (matching the prototype's process
 *     step visualization).
 *   - The client is stateless — all state lives in the consuming hook.
 *   - AbortSignal support for cancellation.
 */

import { apiClient } from "@/api/client";
import {
  AgentEventType,
  type AgentEvent,
  type RunMetadata,
} from "./events";
import { createFeatureLogger } from "@/lib/telemetry";

const log = createFeatureLogger('AgentEventClient');

// ── Step Templates ──────────────────────────────────────────────────────────

/**
 * Predefined step sequences per workspace tab. These represent the logical
 * phases the agent goes through when processing a request. The backend may
 * override these with actual steps in the future.
 */
const TAB_STEP_TEMPLATES: Record<string, Array<{ id: string; label: string }>> = {
  signals: [
    { id: "load-context", label: "Loading account context" },
    { id: "analyze-signals", label: "Analyzing pain signals" },
    { id: "score-confidence", label: "Scoring confidence levels" },
    { id: "synthesize", label: "Synthesizing findings" },
  ],
  drivers: [
    { id: "load-context", label: "Loading account context" },
    { id: "map-drivers", label: "Mapping value drivers" },
    { id: "analyze-hierarchy", label: "Analyzing driver hierarchy" },
    { id: "synthesize", label: "Synthesizing recommendations" },
  ],
  evidence: [
    { id: "load-context", label: "Loading account context" },
    { id: "search-evidence", label: "Searching evidence base" },
    { id: "match-claims", label: "Matching claims to evidence" },
    { id: "synthesize", label: "Synthesizing findings" },
  ],
  stakeholders: [
    { id: "load-context", label: "Loading account context" },
    { id: "map-personas", label: "Mapping buyer personas" },
    { id: "analyze-influence", label: "Analyzing influence network" },
    { id: "synthesize", label: "Synthesizing engagement plan" },
  ],
  "action-plan": [
    { id: "load-context", label: "Loading account context" },
    { id: "evaluate-capabilities", label: "Evaluating product capabilities" },
    { id: "rank-recommendations", label: "Ranking recommendations" },
    { id: "synthesize", label: "Building action plan" },
  ],
  "value-model": [
    { id: "load-context", label: "Loading account context" },
    { id: "gather-inputs", label: "Gathering model inputs" },
    { id: "run-calculations", label: "Running financial calculations" },
    { id: "synthesize", label: "Synthesizing value model" },
  ],
  narrative: [
    { id: "load-context", label: "Loading account context" },
    { id: "analyze-audience", label: "Analyzing target audience" },
    { id: "draft-narrative", label: "Drafting narrative structure" },
    { id: "synthesize", label: "Finalizing narrative" },
  ],
};

const DEFAULT_STEPS = [
  { id: "load-context", label: "Loading context" },
  { id: "process", label: "Processing request" },
  { id: "synthesize", label: "Synthesizing response" },
];

// ── Client ──────────────────────────────────────────────────────────────────

export interface AgentEventClientOptions {
  /** Active workspace tab — determines step templates */
  activeTab: string;
  /** Account context */
  accountId?: string;
  accountName?: string;
  accountTier?: string;
}

/**
 * Send a message to the agent and yield AG-UI events.
 *
 * Currently wraps the existing POST `/agent-stream/chat` endpoint.
 * When the backend adds SSE support, this function can switch to
 * streaming mode without changing the consumer API.
 */
export async function* sendAgentMessage(
  messages: Array<{ role: "system" | "user" | "assistant"; content: string }>,
  options: AgentEventClientOptions,
  signal?: AbortSignal,
): AsyncGenerator<AgentEvent, void, unknown> {
  const runId = `run-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const now = () => new Date().toISOString();
  const steps = TAB_STEP_TEMPLATES[options.activeTab] ?? DEFAULT_STEPS;

  // ── RUN_STARTED ─────────────────────────────────────────────────────────
  yield {
    type: AgentEventType.RUN_STARTED,
    timestamp: now(),
    runId,
    description: `Processing request for ${options.accountName ?? "account"}`,
    expectedSteps: steps,
  };

  // ── Emit STEP_STARTED for all steps (pending → active progression) ────
  // We emit the first step as active immediately
  for (let i = 0; i < steps.length; i++) {
    yield {
      type: AgentEventType.STEP_STARTED,
      timestamp: now(),
      runId,
      stepId: steps[i].id,
      label: steps[i].label,
      index: i,
    };

    // Simulate step completion for all but the last step
    // (the last step completes when we get the response)
    if (i < steps.length - 1) {
      yield {
        type: AgentEventType.STEP_FINISHED,
        timestamp: now(),
        runId,
        stepId: steps[i].id,
        status: "done",
      };
    }
  }

  // ── Call the backend ──────────────────────────────────────────────────
  try {
    const response = (await apiClient.post("l4", "/agent-stream/chat", {
      messages,
      activeTab: options.activeTab,
      account: {
        accountId: options.accountId,
        accountName: options.accountName,
        accountTier: options.accountTier,
      },
    })) as {
      data?: {
        content?: string;
        metadata?: {
          trace_id?: string;
          workflow_id?: string;
          tenant_id?: string;
          audit_event_id?: string;
        };
      };
    };

    if (signal?.aborted) return;

    const data = response.data;
    const content = data?.content ?? "I received your message but couldn't generate a response.";
    const metadata: RunMetadata = {
      traceId: data?.metadata?.trace_id,
      workflowId: data?.metadata?.workflow_id,
      tenantId: data?.metadata?.tenant_id,
      auditEventId: data?.metadata?.audit_event_id,
    };

    // ── Finish the last step ──────────────────────────────────────────
    const lastStep = steps[steps.length - 1];
    yield {
      type: AgentEventType.STEP_FINISHED,
      timestamp: now(),
      runId,
      stepId: lastStep.id,
      status: "done",
    };

    // ── TEXT_MESSAGE sequence ────────────────────────────────────────────
    const messageId = `msg-${Date.now()}`;

    yield {
      type: AgentEventType.TEXT_MESSAGE_START,
      timestamp: now(),
      runId,
      messageId,
      role: "agent",
    };

    yield {
      type: AgentEventType.TEXT_MESSAGE_CONTENT,
      timestamp: now(),
      runId,
      messageId,
      delta: content,
    };

    yield {
      type: AgentEventType.TEXT_MESSAGE_END,
      timestamp: now(),
      runId,
      messageId,
    };

    // ── RUN_FINISHED ──────────────────────────────────────────────────
    yield {
      type: AgentEventType.RUN_FINISHED,
      timestamp: now(),
      runId,
      metadata,
    };
  } catch (error) {
    if (signal?.aborted) return;

    // ── Mark remaining steps as error ─────────────────────────────────
    const lastStep = steps[steps.length - 1];
    yield {
      type: AgentEventType.STEP_FINISHED,
      timestamp: now(),
      runId,
      stepId: lastStep.id,
      status: "error",
    };

    // ── RUN_ERROR ─────────────────────────────────────────────────────
    yield {
      type: AgentEventType.RUN_ERROR,
      timestamp: now(),
      runId,
      message: error instanceof Error ? error.message : "Agent request failed",
      retryable: true,
    };
  }
}

/**
 * Stream AG-UI events from an SSE endpoint.
 *
 * This is the future-ready path for when the backend supports
 * native SSE streaming with AG-UI event format. Currently unused
 * but included so the transport layer is ready.
 */
export async function* streamAgentEvents(
  url: string,
  body: Record<string, unknown>,
  signal?: AbortSignal,
): AsyncGenerator<AgentEvent, void, unknown> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    yield {
      type: AgentEventType.RUN_ERROR,
      timestamp: new Date().toISOString(),
      message: `Server error (${response.status})`,
      retryable: response.status >= 500,
    };
    return;
  }

  if (!response.body) {
    yield {
      type: AgentEventType.RUN_ERROR,
      timestamp: new Date().toISOString(),
      message: "Streaming not supported by this browser",
      retryable: false,
    };
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;

      try {
        const event = JSON.parse(trimmed.slice(6)) as AgentEvent;
        yield event;
      } catch {
        if (import.meta.env.DEV) {
          log.warn('Malformed SSE chunk');
        }
      }
    }
  }
}
