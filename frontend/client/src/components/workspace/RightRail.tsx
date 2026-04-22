/**
 * Right Rail — Contextual Support Panel
 *
 * Two modes:
 *   1. Detail Panel — Inspect a selected entity (signal, driver, evidence item)
 *   2. Agent Stream — Conversational co-pilot with structured actions
 *
 * The right rail is context-aware: it knows which workspace tab is active
 * and adjusts its suggestions accordingly.
 */
import { useState } from "react";
import { cn } from "@/lib/utils";
import { X, MessageSquare, Info, Send } from "lucide-react";
import { Btn } from "@/components/WfPrimitives";

// ── Types ─────────────────────────────────────────────────────────────────────

export type RightRailMode = "detail" | "agent";

export interface DetailPanelProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  onClose?: () => void;
}

export interface AgentMessage {
  id: string;
  role: "agent" | "user";
  content: string;
  timestamp: string;
  actions?: AgentAction[];
}

export interface AgentAction {
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
}

interface RightRailProps {
  mode: RightRailMode;
  onModeChange: (mode: RightRailMode) => void;
  /** Detail panel content — rendered when mode === "detail" */
  detailContent?: React.ReactNode;
  /** Active workspace tab name — used to contextualize agent suggestions */
  activeTab: string;
  /** Agent messages */
  messages: AgentMessage[];
  /** Callback when user sends a message */
  onSendMessage: (message: string) => void;
  /** Suggested actions based on current context */
  suggestedActions?: AgentAction[];
  /** Close handler */
  onClose?: () => void;
}

// ── Mode Toggle ───────────────────────────────────────────────────────────────

function ModeToggle({
  mode,
  onModeChange,
  onClose,
}: {
  mode: RightRailMode;
  onModeChange: (m: RightRailMode) => void;
  onClose?: () => void;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 border-b border-border shrink-0">
      <div className="flex items-center gap-1">
        <button
          onClick={() => onModeChange("detail")}
          className={cn(
            "px-3 py-1 text-[11px] font-semibold rounded-md transition-colors",
            mode === "detail"
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Info size={12} className="inline mr-1" />
          Details
        </button>
        <button
          onClick={() => onModeChange("agent")}
          className={cn(
            "px-3 py-1 text-[11px] font-semibold rounded-md transition-colors",
            mode === "agent"
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <MessageSquare size={12} className="inline mr-1" />
          Agent Stream
        </button>
      </div>
      {onClose && (
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ── Agent Stream ──────────────────────────────────────────────────────────────

function AgentStream({
  messages,
  onSendMessage,
  suggestedActions,
  activeTab,
}: {
  messages: AgentMessage[];
  onSendMessage: (msg: string) => void;
  suggestedActions?: AgentAction[];
  activeTab: string;
}) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <MessageSquare size={24} className="mx-auto text-muted-foreground/50 mb-2" />
            <p className="text-[12px] text-muted-foreground">
              Ask me anything about this {activeTab} view.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "text-[12px] leading-relaxed",
              msg.role === "agent" ? "text-foreground" : "text-foreground"
            )}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-[11px]">
                {msg.role === "agent" ? "ValuePilot" : "You"}
              </span>
              <span className="text-[10px] text-muted-foreground">{msg.timestamp}</span>
            </div>
            <div
              className={cn(
                "rounded-lg px-3 py-2",
                msg.role === "agent"
                  ? "bg-muted/50"
                  : "bg-primary/10 ml-4"
              )}
            >
              {msg.content}
            </div>
            {msg.actions && msg.actions.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {msg.actions.map((action, i) => (
                  <Btn key={i} variant="outline" onClick={action.onClick} className="text-[11px]">
                    {action.icon}
                    {action.label}
                  </Btn>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Suggested actions */}
      {suggestedActions && suggestedActions.length > 0 && (
        <div className="px-4 py-2 border-t border-border flex flex-wrap gap-2">
          {suggestedActions.map((action, i) => (
            <Btn key={i} variant="outline" onClick={action.onClick} className="text-[11px]">
              {action.icon}
              {action.label}
            </Btn>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-4 py-3 border-t border-border shrink-0">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a follow-up…"
            className="flex-1 h-8 px-3 text-[12px] rounded-md border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className={cn(
              "w-8 h-8 rounded-md flex items-center justify-center transition-colors",
              input.trim()
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            )}
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Right Rail ────────────────────────────────────────────────────────────────

export default function RightRail({
  mode,
  onModeChange,
  detailContent,
  activeTab,
  messages,
  onSendMessage,
  suggestedActions,
  onClose,
}: RightRailProps) {
  return (
    <div className="flex flex-col h-full bg-background">
      <ModeToggle mode={mode} onModeChange={onModeChange} onClose={onClose} />

      {mode === "detail" && detailContent && (
        <div className="flex-1 overflow-y-auto p-4">
          {detailContent}
        </div>
      )}

      {mode === "detail" && !detailContent && (
        <div className="flex-1 flex items-center justify-center p-4">
          <p className="text-[12px] text-muted-foreground text-center">
            Select an item to view details.
          </p>
        </div>
      )}

      {mode === "agent" && (
        <AgentStream
          messages={messages}
          onSendMessage={onSendMessage}
          suggestedActions={suggestedActions}
          activeTab={activeTab}
        />
      )}
    </div>
  );
}
