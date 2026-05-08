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
import { AgentEventType, type AgentEvent, type RunMetadata } from "./events";
import { createFeatureLogger } from "@/lib/telemetry";
import { parseAgentEventJson } from "./eventSchemas";

const log = createFeatureLogger("AgentEventClient");

// ── Step Templates ──────────────────────────────────────────────────────────

/**
 * Predefined step sequences per workspace tab. These represent the logical
 * phases the agent goes through when processing a request. The backend may
 * override these with actual steps in the future.
 */
const TAB_STEP_TEMPLATES: Record<
  string,
  Array<{ id: string; label: string }>
> = {
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

type BackendRunMetadata = Record<string, unknown> & {
  run_id?: string;
  trace_id?: string;
  workflow_id?: string;
  tenant_id?: string;
  audit_event_id?: string;
  source_node?: string;
  semantic_contract_version?: string;
  semantic_contract_valid?: boolean;
  semantic_contract_mode?: "warn" | "strict";
  semantic_contract_violations?: unknown[];
};

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function stringField(source: Record<string, unknown>, camel: string, snake?: string): string | undefined {
  const camelValue = source[camel];
  const snakeValue = snake ? source[snake] : undefined;
  return typeof camelValue === "string"
    ? camelValue
    : typeof snakeValue === "string"
      ? snakeValue
      : undefined;
}

function normalizeRunMetadata(raw: BackendRunMetadata | undefined, fallbackRunId: string): RunMetadata {
  const source = raw ?? {};
  const contractVersions = asRecord(source.contractVersions ?? source.contract_versions);
  const provenance = asRecord(source.provenance);

  return {
    ...source,
    runId: stringField(source, "runId", "run_id") ?? fallbackRunId,
    traceId: stringField(source, "traceId", "trace_id") ?? fallbackRunId,
    workflowId: stringField(source, "workflowId", "workflow_id"),
    tenantId: stringField(source, "tenantId", "tenant_id"),
    auditEventId: stringField(source, "auditEventId", "audit_event_id") ?? `audit-${fallbackRunId}`,
    sourceNode: stringField(source, "sourceNode", "source_node"),
    semanticContractVersion: stringField(source, "semanticContractVersion", "semantic_contract_version"),
    semanticContractValid:
      typeof source.semanticContractValid === "boolean"
        ? source.semanticContractValid
        : typeof source.semantic_contract_valid === "boolean"
          ? source.semantic_contract_valid
          : undefined,
    semanticContractMode:
      source.semanticContractMode === "strict" || source.semanticContractMode === "warn"
        ? source.semanticContractMode
        : source.semantic_contract_mode === "strict" || source.semantic_contract_mode === "warn"
          ? source.semantic_contract_mode
          : undefined,
    semanticContractViolations: Array.isArray(source.semanticContractViolations)
      ? (source.semanticContractViolations as RunMetadata["semanticContractViolations"])
      : Array.isArray(source.semantic_contract_violations)
        ? (source.semantic_contract_violations as RunMetadata["semanticContractViolations"])
        : undefined,
    contractVersions: contractVersions as RunMetadata["contractVersions"],
    provenance: provenance as RunMetadata["provenance"],
  };
}

// ── Client ──────────────────────────────────────────────────────────────────

export interface AgentEventClientOptions {
  /** Active workspace tab — determines step templates */
  activeTab: string;
  /** Account context */
  accountId?: string;
  accountName?: string;
  accountTier?: string;
  /** Selected entity context for contextual co-pilot */
  selectedSignalId?: string;
  selectedHypothesisId?: string;
  selectedDriverId?: string;
  selectedEvidenceId?: string;
  selectedValuePath?: string;
  selectedDriverTreeId?: string;
  selectedScenarioId?: string;
  selectedBusinessCaseId?: string;
  workspaceCaseId?: string;
  workflowContext?: Record<string, unknown>;
  entityContext?: Record<string, unknown>;
}

export interface RightRailContextEnvelope {
  accountId: string | null;
  signalId: string | null;
  evidenceId: string | null;
  workspaceTab: string;
}

export function buildRightRailContextEnvelope(options: AgentEventClientOptions): RightRailContextEnvelope {
  return {
    accountId: options.accountId ?? null,
    signalId: options.selectedSignalId ?? null,
    evidenceId: options.selectedEvidenceId ?? null,
    workspaceTab: options.activeTab,
  };
}

/**
 * Send a message to the agent and yield AG-UI events.
 *
 * Uses the SSE streaming endpoint `/agent-stream/chat/stream`.
 * Falls back to the legacy POST `/agent-stream/chat` endpoint if
 * SSE is unavailable (e.g., older backend deployment).
 */
export async function* sendAgentMessage(
  messages: Array<{ role: "system" | "user" | "assistant"; content: string }>,
  options: AgentEventClientOptions,
  signal?: AbortSignal
): AsyncGenerator<AgentEvent, void, unknown> {
  const runId = `run-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const now = () => new Date().toISOString();
  const steps = TAB_STEP_TEMPLATES[options.activeTab] ?? DEFAULT_STEPS;

  // ── Build request body ────────────────────────────────────────────────
  const contextEnvelope = buildRightRailContextEnvelope(options);

  const entityContext = {
    accountId: options.accountId,
    activeTab: options.activeTab,
    selectedSignalId: options.selectedSignalId,
    selectedHypothesisId: options.selectedHypothesisId,
    selectedDriverId: options.selectedDriverId,
    selectedEvidenceId: options.selectedEvidenceId,
    selectedValuePath: options.selectedValuePath,
    selectedDriverTreeId: options.selectedDriverTreeId,
    selectedScenarioId: options.selectedScenarioId,
    selectedBusinessCaseId: options.selectedBusinessCaseId,
    workspaceCaseId: options.workspaceCaseId,
    workflowContext: options.workflowContext,
    ...(options.entityContext ?? {}),
    contextEnvelope,
  };

  const body = {
    messages,
    activeTab: options.activeTab,
    account: {
      accountId: options.accountId,
      accountName: options.accountName,
      accountTier: options.accountTier,
    },
    contextEnvelope,
    entityContext,
    selectedSignalId: options.selectedSignalId,
    selectedValuePath: options.selectedValuePath,
    selectedDriverTreeId: options.selectedDriverTreeId,
    selectedScenarioId: options.selectedScenarioId,
    selectedBusinessCaseId: options.selectedBusinessCaseId,
  };

  // ── Try SSE streaming first ───────────────────────────────────────────
  try {
    const prefix = import.meta.env.VITE_L4_PREFIX || "/agents";
    const base = import.meta.env.VITE_API_BASE || "/api/v1";
    const url = `${base}${prefix}/agent-stream/chat/stream`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": localStorage.getItem("tenantId") || "default",
      },
      body: JSON.stringify(body),
      signal,
    });

    if (response.ok && response.headers.get("content-type")?.includes("text/event-stream")) {
      // Backend supports SSE — consume the stream
      const stream = streamAgentEventsFromResponse(response, signal);
      for await (const event of stream) {
        yield event;
      }
      return;
    }

    // If SSE endpoint returns 404 or non-SSE, fall through to legacy mode
    if (response.status !== 404) {
      // Unexpected error from SSE endpoint
      const text = await response.text().catch(() => "Unknown error");
      throw new Error(`SSE endpoint error (${response.status}): ${text}`);
    }
  } catch (error) {
    // 404 or network error — fall back to legacy POST endpoint
    if (import.meta.env.DEV) {
      log.info("SSE stream unavailable, falling back to legacy POST", {
        errorCode: error instanceof Error ? error.message : String(error),
      });
    }
  }

  // ── Legacy fallback: synthesize events from single POST response ──────
  yield {
    type: AgentEventType.RUN_STARTED,
    timestamp: now(),
    runId,
    description: `Processing request for ${options.accountName ?? "account"}`,
    expectedSteps: steps,
  };

  for (let i = 0; i < steps.length; i++) {
    yield {
      type: AgentEventType.STEP_STARTED,
      timestamp: now(),
      runId,
      stepId: steps[i].id,
      label: steps[i].label,
      index: i,
    };
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

  try {
    const response = (await apiClient.post("l4", "/agent-stream/chat", body)) as {
      data?: {
        content?: string;
        metadata?: BackendRunMetadata;
        actions?: Array<{
          label: string;
          page_action: {
            entityType: "signal" | "evidence" | "hypothesis" | "scenario";
            entityId: string;
            accountId: string;
            caseId: string;
            tenantId?: string;
            intendedOperation: "signal_review" | "evidence_attach" | "hypothesis_convert" | "scenario_update";
            payload?: Record<string, unknown>;
          };
        }>;
      };
    };

    if (signal?.aborted) return;

    const data = response.data;
    const content =
      data?.content ??
      "I received your message but couldn't generate a response.";
    const metadata = normalizeRunMetadata(data?.metadata, runId);

    const lastStep = steps[steps.length - 1];
    yield {
      type: AgentEventType.STEP_FINISHED,
      timestamp: now(),
      runId,
      stepId: lastStep.id,
      status: "done",
    };

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
    yield {
      type: AgentEventType.RUN_FINISHED,
      timestamp: now(),
      runId,
      output: { actions: data?.actions ?? [] },
      metadata,
    };
  } catch (error) {
    if (signal?.aborted) return;
    const lastStep = steps[steps.length - 1];
    yield {
      type: AgentEventType.STEP_FINISHED,
      timestamp: now(),
      runId,
      stepId: lastStep.id,
      status: "error",
    };
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
 * Consume AG-UI events from an already-opened fetch Response.
 */
async function* streamAgentEventsFromResponse(
  response: Response,
  signal?: AbortSignal
): AsyncGenerator<AgentEvent, void, unknown> {
  if (!response.body) {
    yield {
      type: AgentEventType.RUN_ERROR,
      timestamp: new Date().toISOString(),
      message: "Streaming not supported",
      retryable: false,
    };
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      if (signal?.aborted) return;
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data: ")) continue;

        try {
          const event = parseAgentEventJson(trimmed.slice(6));
          yield event;
        } catch {
          if (import.meta.env.DEV) {
            log.warn("Malformed SSE chunk");
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
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
  signal?: AbortSignal
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
        yield parseAgentEventJson(trimmed.slice(6));
      } catch {
        if (import.meta.env.DEV) {
          log.warn("Malformed SSE chunk");
        }
      }
    }
  }
}
