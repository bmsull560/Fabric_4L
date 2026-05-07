/**
 * useAgentStream — Shared hook for the Agent Stream co-pilot
 *
 * @deprecated Prefer `useAgentEvents` from `@/agui` for new code.
 * This hook is retained for backward compatibility with existing
 * workspace tabs that haven't migrated to AG-UI events yet.
 * The `getDefaultSuggestedActions` export is still used by
 * useAgentEvents and should remain here.
 *
 * Migration path:
 *   Old: const { messages, sendMessage, isStreaming, suggestedActions } = useAgentStream({ ... });
 *   New: const { messages, sendMessage, isStreaming, suggestedActions, steps, runState } = useAgentEvents({ ... });
 *
 * Provides real natural-language interaction by calling the backend
 * agent endpoint (or falling back to the OpenAI-compatible API).
 *
 * Context-aware: the hook receives the active workspace tab name
 * and account context so the agent can tailor its responses.
 */
import { useState, useCallback } from "react";
import type { AgentMessage, AgentAction } from "@/components/workspace/RightRail";
import { apiClient } from "@/api/client";

// ── System Prompts by Tab ────────────────────────────────────────────────────

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

// ── Suggested Actions by Tab ─────────────────────────────────────────────────

export function getDefaultSuggestedActions(
  activeTab: string,
  sendMessage?: (input: string) => void,
): AgentAction[] {
  const send = sendMessage ?? (() => {});
  switch (activeTab) {
    case "signals":
      return [
        { label: "Generate value driver tree", onClick: () => send("Generate a value driver tree from the current signals") },
        { label: "Summarize evidence", onClick: () => send("Summarize the evidence for the top signals") },
        { label: "Draft action plan", onClick: () => send("Draft an action plan based on these signals") },
        { label: "Compare all signals", onClick: () => send("Compare all signals by confidence and impact") },
      ];
    case "drivers":
      return [
        { label: "Map to product capabilities", onClick: () => send("Map these drivers to our product capabilities") },
        { label: "Find missing drivers", onClick: () => send("Are there any missing drivers we should consider?") },
        { label: "Prioritize by impact", onClick: () => send("Prioritize the drivers by estimated business impact") },
      ];
    case "evidence":
      return [
        { label: "Find more evidence", onClick: () => send("Find additional evidence to support our claims") },
        { label: "Audit weak claims", onClick: () => send("Audit the claims and flag any that need stronger evidence") },
        { label: "Export evidence summary", onClick: () => send("Create an evidence summary I can export") },
      ];
    case "stakeholders":
      return [
        { label: "Suggest messaging angles", onClick: () => send("Suggest messaging angles for each stakeholder") },
        { label: "Identify missing buyers", onClick: () => send("Identify any missing buyer personas we should engage") },
        { label: "Map influence network", onClick: () => send("Map the influence network among these stakeholders") },
      ];
    case "action-plan":
      return [
        { label: "Strengthen proof points", onClick: () => send("Strengthen the proof points in this action plan") },
        { label: "Re-prioritize recommendations", onClick: () => send("Re-prioritize the recommendations by urgency") },
        { label: "Add custom recommendation", onClick: () => send("Suggest a custom recommendation for this account") },
      ];
    case "value-model":
      return [
        { label: "Run sensitivity analysis", onClick: () => send("Run a sensitivity analysis on the value model") },
        { label: "Compare scenarios", onClick: () => send("Compare the optimistic, pessimistic, and base case scenarios") },
        { label: "Validate assumptions", onClick: () => send("Validate the key assumptions in this value model") },
      ];
    case "narrative":
      return [
        { label: "Adjust for CFO audience", onClick: () => send("Adjust this narrative for a CFO audience") },
        { label: "Shorten executive summary", onClick: () => send("Shorten the executive summary to under 100 words") },
        { label: "Add competitive positioning", onClick: () => send("Add competitive positioning to the narrative") },
      ];
    default:
      return [];
  }
}

// ── Hook ─────────────────────────────────────────────────────────────────────

interface UseAgentStreamOptions {
  activeTab: string;
  accountId?: string;
  accountName?: string;
  accountTier?: string;
  initialMessages?: AgentMessage[];
}

export function useAgentStream({
  activeTab,
  accountId,
  accountName = "this account",
  accountTier,
  initialMessages,
}: UseAgentStreamOptions) {
  const [messages, setMessages] = useState<AgentMessage[]>(
    initialMessages ?? [
      {
        id: "welcome",
        role: "agent",
        content: `I'm ready to help you with the ${activeTab} view for ${accountName}. What would you like to explore?`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]
  );
  const [isStreaming, setIsStreaming] = useState(false);

  const devFallbackEnabled =
    import.meta.env.DEV && import.meta.env.VITE_AGENT_STREAM_DEV_FALLBACK === "true";

  const sendMessage = useCallback(
    async (userInput: string) => {
      // Add user message
      const userMsg: AgentMessage = {
        id: `u-${Date.now()}`,
        role: "user",
        content: userInput,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);

      try {
        const systemPrompt =
          TAB_SYSTEM_PROMPTS[activeTab] ??
          "You are ValuePilot, an AI co-pilot for value selling. Keep responses concise.";

        const conversationMessages = [
          { role: "system" as const, content: systemPrompt },
          ...messages.slice(-10).map((m) => ({
            role: m.role === "agent" ? ("assistant" as const) : ("user" as const),
            content: m.content,
          })),
          { role: "user" as const, content: userInput },
        ];

        const response = (await apiClient.post("l4", "/agent-stream/chat", {
          messages: conversationMessages,
          activeTab,
          account: {
            accountId,
            accountName,
            accountTier,
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

        const data = response.data;
        const agentContent =
          data?.content ?? "I received your message but couldn't generate a response.";

        const agentMsg: AgentMessage = {
          id: `a-${Date.now()}`,
          role: "agent",
          content: agentContent,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          metadata: {
            traceId: data?.metadata?.trace_id,
            workflowId: data?.metadata?.workflow_id,
            tenantId: data?.metadata?.tenant_id,
            auditEventId: data?.metadata?.audit_event_id,
          },
        };
        setMessages((prev) => [...prev, agentMsg]);
      } catch {
        if (!devFallbackEnabled) {
          const errorMsg: AgentMessage = {
            id: `a-${Date.now()}`,
            role: "agent",
            content:
              "I couldn't reach the agent service right now. Please retry in a moment.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };
          setMessages((prev) => [...prev, errorMsg]);
          return;
        }

        const fallbackMsg: AgentMessage = {
          id: `a-${Date.now()}`,
          role: "agent",
          content: generateFallbackResponse(activeTab, userInput),
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, fallbackMsg]);
      } finally {
        setIsStreaming(false);
      }
    },
    [activeTab, accountId, accountName, accountTier, devFallbackEnabled, messages]
  );

  const suggestedActions = getDefaultSuggestedActions(activeTab, sendMessage);

  return { messages, sendMessage, isStreaming, suggestedActions };
}

// ── Fallback Response Generator ──────────────────────────────────────────────

function generateFallbackResponse(activeTab: string, userInput: string): string {
  const input = userInput.toLowerCase();

  if (input.includes("summarize") || input.includes("summary")) {
    return `Here's a summary of the current ${activeTab} data. The analysis shows several key findings that warrant attention. I recommend reviewing the highest-confidence items first and validating them with available evidence before proceeding to the value model.`;
  }
  if (input.includes("compare")) {
    return `Comparing the items in the ${activeTab} view: the top-ranked items show significantly higher confidence and impact scores. The gap between the first and second items suggests a clear priority for the value case.`;
  }
  if (input.includes("recommend") || input.includes("suggest") || input.includes("next")) {
    return `Based on the current ${activeTab} analysis, I recommend: (1) Validate the top signals with the prospect, (2) Map the strongest drivers to your product capabilities, and (3) Build the action plan around the highest-confidence items.`;
  }
  if (input.includes("help") || input.includes("what can you")) {
    return `In the ${activeTab} view, I can help you analyze data, compare items, generate summaries, suggest next steps, and refine your value case. Just ask me a specific question about what you see.`;
  }

  return `I understand you're asking about "${userInput}" in the context of ${activeTab}. The backend agent service isn't connected yet, but once it is, I'll be able to provide detailed analysis based on the account's intelligence data and your product's value packs.`;
}
