/**
 * HypothesesTab — Value Hypothesis Explorer
 *
 * DIL-backed tab wired to the Value Hypothesis Engine (L4).
 * Uses: useAccountHypotheses, useGenerateHypotheses, useValidateHypothesis
 *       from useHypotheses hook.
 *
 * Shows generated value hypotheses ranked by confidence, with status
 * lifecycle management (draft → validated → converted).
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Lightbulb,
  Sparkles,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Loader2,
  Filter,
  Target,
} from "lucide-react";
import HypothesisShell from "@/components/workspace/HypothesisShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import {
  useAccountHypotheses,
  useGenerateHypotheses,
  useValidateHypothesis,
  type ValueHypothesis,
} from "@/hooks/useHypotheses";

// ── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof Lightbulb }> = {
  draft:     { label: "Draft",     color: "text-muted-foreground", icon: Lightbulb },
  validated: { label: "Validated", color: "text-green-600",        icon: CheckCircle2 },
  rejected:  { label: "Rejected",  color: "text-red-500",          icon: XCircle },
  converted: { label: "Converted", color: "text-primary",          icon: ArrowRight },
};

function confidenceBar(score: number) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-muted rounded-full h-1.5">
        <div
          className={cn("h-1.5 rounded-full", {
            "bg-green-500": pct >= 70,
            "bg-amber-500": pct >= 40 && pct < 70,
            "bg-red-500": pct < 40,
          })}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] font-semibold">{pct}%</span>
    </div>
  );
}

// ── Hypothesis Card ──────────────────────────────────────────────────────────

function HypothesisCard({
  hypothesis,
  isSelected,
  onSelect,
  onStatusChange,
  isUpdating,
}: {
  hypothesis: ValueHypothesis;
  isSelected: boolean;
  onSelect: () => void;
  onStatusChange: (status: "validated" | "rejected") => void;
  isUpdating: boolean;
}) {
  const cfg = STATUS_CONFIG[hypothesis.status] ?? STATUS_CONFIG.draft;
  const Icon = cfg.icon;

  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex flex-col gap-2 w-full px-4 py-3 rounded-md text-left transition-colors",
        isSelected ? "bg-primary/5 ring-1 ring-primary/20" : "hover:bg-muted/50"
      )}
    >
      <div className="flex items-start gap-3 w-full">
        <Icon size={14} className={cn("mt-0.5 shrink-0", cfg.color)} />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold">{hypothesis.value_driver}</div>
          <div className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">
            {hypothesis.hypothesis_text}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {confidenceBar(hypothesis.confidence)}
          <span className={cn("text-[10px] font-semibold", cfg.color)}>{cfg.label}</span>
        </div>
      </div>

      {/* Signal → Product mapping */}
      <div className="flex items-center gap-1.5 ml-7 text-[10px] text-muted-foreground">
        <Target size={10} />
        <span className="truncate">{hypothesis.signal_ids.length} signal(s)</span>
        <ArrowRight size={8} />
        <span className="font-medium text-foreground truncate">Product {hypothesis.product_id}</span>
      </div>

      {/* Quick actions */}
      {isSelected && hypothesis.status === "draft" && (
        <div className="flex items-center gap-2 ml-7 mt-1">
          <button
            onClick={(e) => { e.stopPropagation(); onStatusChange("validated"); }}
            disabled={isUpdating}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-green-50 text-green-700 hover:bg-green-100 disabled:opacity-50"
          >
            <CheckCircle2 size={10} /> Validate
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onStatusChange("rejected"); }}
            disabled={isUpdating}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50"
          >
            <XCircle size={10} /> Reject
          </button>
        </div>
      )}
    </button>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function HypothesesTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const {
    data: hypothesesData,
    isLoading,
    error,
  } = useAccountHypotheses(accountId ?? null);
  const generateHypotheses = useGenerateHypotheses();
  const validateHypothesis = useValidateHypothesis();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [railMode, setRailMode] = useState<RightRailMode>("detail");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "hypotheses",
    accountName: account?.name ?? "Account",
  });

  const hypotheses: ValueHypothesis[] = hypothesesData?.hypotheses ?? [];
  const selected = hypotheses.find((h) => h.id === selectedId) ?? null;

  // Filter
  const filtered =
    statusFilter === "all"
      ? hypotheses
      : hypotheses.filter((h) => h.status === statusFilter);

  // Stats
  const validated = hypotheses.filter((h) => h.status === "validated").length;
  const avgConfidence = hypotheses.length
    ? hypotheses.reduce((sum, h) => sum + h.confidence, 0) / hypotheses.length
    : 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-sm text-muted-foreground">
        <Loader2 size={16} className="animate-spin" />
        Loading value hypotheses…
      </div>
    );
  }

  if (error) {
    return <div className="p-6 text-sm text-destructive">Failed to load hypotheses.</div>;
  }

  return (
    <HypothesisShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue
          ? `$${account.annual_revenue.toLocaleString()}`
          : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="hypotheses"
          detailContent={
            selected ? (
              <div className="space-y-3">
                <h3 className="text-sm font-bold">{selected.value_driver}</h3>
                <p className="text-xs text-muted-foreground">{selected.hypothesis_text}</p>
                <div className="space-y-2 text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Confidence</span>
                    <span className="font-semibold">{Math.round(selected.confidence * 100)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Product ID</span>
                    <span className="font-semibold">{selected.product_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <span className="font-semibold">{selected.status}</span>
                  </div>
                </div>
                {selected.evidence_ids && selected.evidence_ids.length > 0 && (
                  <div className="text-[10px] text-muted-foreground">
                    {selected.evidence_ids.length} evidence item(s) linked
                  </div>
                )}
                {selected.validation_notes && (
                  <div className="text-[10px] text-muted-foreground border-t pt-2">
                    <span className="font-semibold">Notes:</span> {selected.validation_notes}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                Select a hypothesis to view details.
              </div>
            )
          }
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
            steps={steps}
            isStreaming={isStreaming}
            runMetadata={metadata}
        />
      }
    >
      {/* Header metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard label="Total Hypotheses" value={String(hypotheses.length)} />
        <MetricCard
          label="Validated"
          value={String(validated)}
          trend={`${hypotheses.length ? Math.round((validated / hypotheses.length) * 100) : 0}%`}
        />
        <MetricCard
          label="Avg Confidence"
          value={`${Math.round(avgConfidence * 100)}%`}
        />
        <MetricCard
          label="Products Mapped"
          value={String(new Set(hypotheses.map((h) => h.product_id)).size)}
        />
      </div>

      {/* Actions bar */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => {
            if (accountId) {
              generateHypotheses.mutate({
                account_id: accountId,
                max_hypotheses: 20,
              });
            }
          }}
          disabled={generateHypotheses.isPending}
          className={cn(
            "inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold transition-colors",
            "bg-primary text-primary-foreground hover:bg-primary/90",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          {generateHypotheses.isPending ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Sparkles size={14} />
          )}
          {generateHypotheses.isPending ? "Generating…" : "Generate Hypotheses"}
        </button>

        {/* Status filter */}
        <div className="flex items-center gap-1 ml-auto">
          <Filter size={12} className="text-muted-foreground" />
          {["all", "draft", "validated", "rejected", "converted"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                "px-2 py-0.5 rounded text-[10px] font-semibold transition-colors",
                statusFilter === s
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {s === "all" ? "All" : (STATUS_CONFIG[s]?.label ?? s)}
            </button>
          ))}
        </div>
      </div>

      {/* Hypothesis list */}
      {filtered.length === 0 ? (
        <SectionCard title="Value Hypotheses">
          <div className="text-center py-8">
            <Lightbulb size={32} className="mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground mb-2">
              {hypotheses.length === 0
                ? "No hypotheses generated yet."
                : "No hypotheses match the current filter."}
            </p>
            {hypotheses.length === 0 && (
              <p className="text-xs text-muted-foreground">
                Click "Generate Hypotheses" to discover value opportunities from signals.
              </p>
            )}
          </div>
        </SectionCard>
      ) : (
        <SectionCard title={`Value Hypotheses (${filtered.length})`}>
          <div className="space-y-1">
            {filtered.map((h) => (
              <HypothesisCard
                key={h.id}
                hypothesis={h}
                isSelected={selectedId === h.id}
                onSelect={() => setSelectedId(h.id)}
                onStatusChange={(status) => {
                  validateHypothesis.mutate({ hypothesisId: h.id, data: { status } });
                }}
                isUpdating={validateHypothesis.isPending}
              />
            ))}
          </div>
        </SectionCard>
      )}
    </HypothesisShell>
  );
}
