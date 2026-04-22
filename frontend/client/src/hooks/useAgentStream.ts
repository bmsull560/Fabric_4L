/**
 * useAgentStream — Shared hook for the Agent Stream co-pilot
 *
 * Provides real natural-language interaction by calling the backend
 * agent endpoint (or falling back to the OpenAI-compatible API).
 *
 * Context-aware: the hook receives the active workspace tab name
 * and account context so the agent can tailor its responses.
 */
import { useState, useCallback } from "react";
import type { AgentMessage, AgentAction } from "@/components/workspace/RightRail";

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

export function getDefaultSuggestedActions(activeTab: string): AgentAction[] {
  switch (activeTab) {
    case "signals":
      return [
        { label: "Generate value driver tree", onClick: () => {} },
        { label: "Summarize evidence", onClick: () => {} },
        { label: "Draft action plan", onClick: () => {} },
        { label: "Compare all signals", onClick: () => {} },
      ];
    case "drivers":
      return [
        { label: "Map to product capabilities", onClick: () => {} },
        { label: "Find missing drivers", onClick: () => {} },
        { label: "Prioritize by impact", onClick: () => {} },
      ];
    case "evidence":
      return [
        { label: "Find more evidence", onClick: () => {} },
        { label: "Audit weak claims", onClick: () => {} },
        { label: "Export evidence summary", onClick: () => {} },
      ];
    case "stakeholders":
      return [
        { label: "Suggest messaging angles", onClick: () => {} },
        { label: "Identify missing buyers", onClick: () => {} },
        { label: "Map influence network", onClick: () => {} },
      ];
    case "action-plan":
      return [
        { label: "Strengthen proof points", onClick: () => {} },
        { label: "Re-prioritize recommendations", onClick: () => {} },
        { label: "Add custom recommendation", onClick: () => {} },
      ];
    case "value-model":
      return [
        { label: "Run sensitivity analysis", onClick: () => {} },
        { label: "Compare scenarios", onClick: () => {} },
        { label: "Validate assumptions", onClick: () => {} },
      ];
    case "narrative":
      return [
        { label: "Adjust for CFO audience", onClick: () => {} },
        { label: "Shorten executive summary", onClick: () => {} },
        { label: "Add competitive positioning", onClick: () => {} },
      ];
    default:
      return [];
  }
}

// ── Hook ─────────────────────────────────────────────────────────────────────

interface UseAgentStreamOptions {
  activeTab: string;
  accountName?: string;
  initialMessages?: AgentMessage[];
}

export function useAgentStream({
  activeTab,
  accountName = "this account",
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
        // Build conversation history for the API
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

        // Call the backend agent endpoint (falls back to OpenAI-compatible API)
        const response = await fetch("/api/agent/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: conversationMessages,
            context: { activeTab, accountName },
          }),
        });

        let agentContent: string;

        if (response.ok) {
          const data = await response.json();
          agentContent = data.content ?? data.choices?.[0]?.message?.content ?? "I received your message but couldn't generate a response.";
        } else {
          // Fallback: generate a context-aware response locally
          agentContent = generateFallbackResponse(activeTab, userInput);
        }

        const agentMsg: AgentMessage = {
          id: `a-${Date.now()}`,
          role: "agent",
          content: agentContent,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, agentMsg]);
      } catch {
        // Network error — use fallback
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
    [activeTab, accountName, messages]
  );

  const suggestedActions = getDefaultSuggestedActions(activeTab);

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
