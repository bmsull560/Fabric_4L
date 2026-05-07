/**
 * useAgentEvents — React hook for AG-UI protocol event consumption.
 *
 * This hook replaces `useAgentStream` as the primary interface between
 * workspace tabs and the agent co-pilot. It exposes:
 *
 *   - `messages`         : Chat history (same shape as before for backward compat)
 *   - `steps`            : Current run's step progression (for ProcessSteps component)
 *   - `runState`         : Lifecycle state (idle | running | finished | error)
 *   - `sendMessage`      : Send a user message and trigger an agent run
 *   - `suggestedActions`  : Context-aware action buttons
 *   - `currentRunId`     : Active run correlation ID
 *   - `lastError`        : Most recent error message
 *   - `metadata`         : Run metadata (trace, workflow, tenant IDs)
 *
 * UI Contract (Behavior):
 *   - Calling `sendMessage` transitions runState: idle → running → finished|error
 *   - Steps progress from pending → active → done as events arrive
 *   - Messages accumulate across runs (conversation history)
 *   - The hook is fully backward-compatible with the RightRail props interface
 *
 * UI Contract (Data):
 *   - `messages` array uses the same `AgentMessage` type from RightRail
 *   - `steps` array uses `StepSnapshot` from AG-UI events
 *   - `suggestedActions` uses the same `AgentAction` type from RightRail
 */

import { useState, useCallback, useRef, useEffect } from "react";
import type { AgentMessage, AgentAction } from "@/components/workspace/RightRail";
import {
  AgentEventType,
  type AgentEvent,
  type StepSnapshot,
  type RunMetadata,
} from "./events";
import { sendAgentMessage } from "./AgentEventClient";
import { getDefaultSuggestedActions } from "@/hooks/useAgentStream";

// ── Tab System Prompts (reused from useAgentStream) ─────────────────────────

const TAB_SYSTEM_PROMPTS: Record<string, string> = {
  signals: `You are ValuePilot, an AI co-pilot embedded in the Intelligence → Signals workspace.
You help sales engineers analyze AI-surfaced pain signals for a prospect account.
You can summarize signals, compare them, explain confidence scores, suggest which signals
to prioritize, and recommend next steps like generating a value driver tree or drafting
an action plan. Keep responses concise (2-3 sentences max) and actionable.`,

  drivers: `You are ValuePilot, an AI co-pilot embedded in the Intelligence → Drivers workspace.
You help sales engineers understand root cause analysis connecting prospect pain signals
to underlying business drivers. You can explain driver hierarchies, suggest missing drivers,
and help map drivers to product capabilities. Keep responses concise and actionable.`,

  evidence: `You are ValuePilot, an AI co-pilot embedded in the Intelligence → Evidence workspace.
You help sales engineers validate claims with source documents, benchmarks, and case studies.
You can explain evidence match scores, suggest additional evidence sources, and flag claims
that need stronger proof. Keep responses concise and actionable.`,

  stakeholders: `You are ValuePilot, an AI co-pilot embedded in the Intelligence → Stakeholders workspace.
You help sales engineers map buyer personas and understand stakeholder priorities.
You can suggest messaging angles for different roles, identify missing stakeholders,
and recommend engagement strategies. Keep responses concise and actionable.`,

  "action-plan": `You are ValuePilot, an AI co-pilot embedded in the Value Studio → Action Plan workspace.
You help sales engineers build product-anchored recommendations that map validated prospect
pain to specific product capabilities. You can refine recommendations, adjust priorities,
and strengthen the "why us" argument. Keep responses concise and actionable.`,

  "value-model": `You are ValuePilot, an AI co-pilot embedded in the Value Studio → Value Model workspace.
You help sales engineers build and refine quantified business cases. You can explain
financial projections, adjust assumptions, compare scenarios, and validate calculations.
Keep responses concise and actionable.`,

  narrative: `You are ValuePilot, an AI co-pilot embedded in the Value Studio → Narrative workspace.
You help sales engineers package the value case for stakeholder presentations.
You can refine messaging, adjust tone for different audiences, and suggest narrative
structures. Keep responses concise and actionable.`,
};

// ── Run State ───────────────────────────────────────────────────────────────

export type RunState = "idle" | "running" | "finished" | "error";

// ── Hook Options ────────────────────────────────────────────────────────────

export interface UseAgentEventsOptions {
  /** Active workspace tab — determines system prompt and step templates */
  activeTab: string;
  /** Account context */
  accountId?: string;
  accountName?: string;
  accountTier?: string;
  /** Selected entity context for contextual co-pilot */
  selectedSignalId?: string;
  selectedValuePath?: string;
  selectedDriverTreeId?: string;
  selectedScenarioId?: string;
  selectedBusinessCaseId?: string;
  /** Initial messages (e.g. restored from session) */
  initialMessages?: AgentMessage[];
}

// ── Hook Return ─────────────────────────────────────────────────────────────

export interface UseAgentEventsReturn {
  /** Chat message history (backward-compatible with RightRail) */
  messages: AgentMessage[];
  /** Current run's step progression */
  steps: StepSnapshot[];
  /** Lifecycle state of the current/last run */
  runState: RunState;
  /** Send a user message and trigger an agent run */
  sendMessage: (input: string) => void;
  /** Context-aware suggested actions */
  suggestedActions: AgentAction[];
  /** Active run correlation ID */
  currentRunId: string | null;
  /** Most recent error message */
  lastError: string | null;
  /** Run metadata from the last completed run */
  metadata: RunMetadata | null;
  /** Whether the agent is actively processing (alias for runState === "running") */
  isStreaming: boolean;
}

// ── Hook Implementation ─────────────────────────────────────────────────────

export function useAgentEvents({
  activeTab,
  accountId,
  accountName = "this account",
  accountTier,
  selectedSignalId,
  selectedValuePath,
  selectedDriverTreeId,
  selectedScenarioId,
  selectedBusinessCaseId,
  initialMessages,
}: UseAgentEventsOptions): UseAgentEventsReturn {
  const [messages, setMessages] = useState<AgentMessage[]>(
    initialMessages ?? [
      {
        id: "welcome",
        role: "agent",
        content: `I'm ready to help you with the ${activeTab} view for ${accountName}. What would you like to explore?`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ],
  );

  const [steps, setSteps] = useState<StepSnapshot[]>([]);
  const [runState, setRunState] = useState<RunState>("idle");
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<RunMetadata | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // ── Event Reducer ───────────────────────────────────────────────────────

  const processEvent = useCallback((event: AgentEvent) => {
    switch (event.type) {
      case AgentEventType.RUN_STARTED: {
        setCurrentRunId(event.runId ?? null);
        setRunState("running");
        setLastError(null);
        // Initialize steps from expectedSteps
        if (event.expectedSteps) {
          setSteps(
            event.expectedSteps.map((s) => ({
              id: s.id,
              label: s.label,
              status: "pending",
            })),
          );
        }
        break;
      }

      case AgentEventType.STEP_STARTED: {
        setSteps((prev) =>
          prev.map((s) =>
            s.id === event.stepId
              ? { ...s, status: "active", startedAt: event.timestamp }
              : s,
          ),
        );
        break;
      }

      case AgentEventType.STEP_FINISHED: {
        setSteps((prev) =>
          prev.map((s) =>
            s.id === event.stepId
              ? { ...s, status: event.status, finishedAt: event.timestamp, result: event.result }
              : s,
          ),
        );
        break;
      }

      case AgentEventType.TEXT_MESSAGE_CONTENT: {
        // For non-streaming (single delta), add the full message
        const agentMsg: AgentMessage = {
          id: event.messageId,
          role: "agent",
          content: event.delta,
          timestamp: new Date(event.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
        setMessages((prev) => {
          // If we already have this messageId, append to it (streaming)
          const existing = prev.find((m) => m.id === event.messageId);
          if (existing) {
            return prev.map((m) =>
              m.id === event.messageId
                ? { ...m, content: m.content + event.delta }
                : m,
            );
          }
          return [...prev, agentMsg];
        });
        break;
      }

      case AgentEventType.TEXT_MESSAGE_START: {
        // Pre-create an empty message placeholder for streaming
        const placeholder: AgentMessage = {
          id: event.messageId,
          role: "agent",
          content: "",
          timestamp: new Date(event.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
        setMessages((prev) => [...prev, placeholder]);
        break;
      }

      case AgentEventType.RUN_FINISHED: {
        setRunState("finished");
        if (event.metadata) {
          setMetadata(event.metadata);
        }
        break;
      }

      case AgentEventType.RUN_ERROR: {
        setRunState("error");
        setLastError(event.message);
        // Add error message to chat
        const errorMsg: AgentMessage = {
          id: `err-${Date.now()}`,
          role: "agent",
          content: event.retryable
            ? `I couldn't complete that request: ${event.message}. Please try again.`
            : `An error occurred: ${event.message}`,
          timestamp: new Date(event.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
        setMessages((prev) => [...prev, errorMsg]);
        break;
      }

      case AgentEventType.TOOL_CALL_START: {
        // Surface tool calls as a custom step
        setSteps((prev) => [
          ...prev,
          {
            id: event.toolCallId,
            label: `Calling ${event.toolName}`,
            status: "active",
            startedAt: event.timestamp,
          },
        ]);
        break;
      }

      case AgentEventType.TOOL_CALL_END: {
        setSteps((prev) =>
          prev.map((s) =>
            s.id === event.toolCallId
              ? {
                  ...s,
                  status: event.success ? "done" : "error",
                  finishedAt: event.timestamp,
                  result: event.result,
                }
              : s,
          ),
        );
        break;
      }

      // STATE_DELTA, STATE_SNAPSHOT, CUSTOM — extensible, no-op for now
      default:
        break;
    }
  }, []);

  // ── Send Message ────────────────────────────────────────────────────────

  const sendMessage = useCallback(
    (userInput: string) => {
      // Abort any in-flight run
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      // Add user message to chat
      const userMsg: AgentMessage = {
        id: `u-${Date.now()}`,
        role: "user",
        content: userInput,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Build conversation context
      const systemPrompt =
        TAB_SYSTEM_PROMPTS[activeTab] ??
        "You are ValuePilot, an AI co-pilot for value selling. Keep responses concise.";

      const conversationMessages: Array<{ role: "system" | "user" | "assistant"; content: string }> = [
        { role: "system", content: systemPrompt },
        ...messages.slice(-10).map((m) => ({
          role: (m.role === "agent" ? "assistant" : "user") as "system" | "user" | "assistant",
          content: m.content,
        })),
        { role: "user", content: userInput },
      ];

      // Consume the event stream
      (async () => {
        try {
          const stream = sendAgentMessage(
            conversationMessages,
            {
              activeTab,
              accountId,
              accountName,
              accountTier,
              selectedSignalId,
              selectedValuePath,
              selectedDriverTreeId,
              selectedScenarioId,
              selectedBusinessCaseId,
            },
            abortRef.current?.signal,
          );

          for await (const event of stream) {
            if (abortRef.current?.signal.aborted) break;
            processEvent(event);
          }
        } catch (error) {
          if (abortRef.current?.signal.aborted) return;
          setRunState("error");
          setLastError(error instanceof Error ? error.message : "Unknown error");
        }
      })();
    },
    [activeTab, accountId, accountName, accountTier, selectedSignalId, selectedValuePath, selectedDriverTreeId, selectedScenarioId, selectedBusinessCaseId, messages, processEvent],
  );

  // ── Suggested Actions ─────────────────────────────────────────────────

  const suggestedActions = getDefaultSuggestedActions(activeTab, sendMessage);

  return {
    messages,
    steps,
    runState,
    sendMessage,
    suggestedActions,
    currentRunId,
    lastError,
    metadata,
    isStreaming: runState === "running",
  };
}
