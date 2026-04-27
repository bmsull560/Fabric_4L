/**
 * Action Plan Tab — Enhanced with DIL hooks
 *
 * Primary data: workspace case recommendations (existing)
 * DIL enrichment: value hypotheses + product portfolio for richer context
 */
import { useEffect, useMemo, useState } from "react";
import { useParams } from "wouter";
import { ChevronDown, ChevronUp, Lightbulb, Package, Sparkles } from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useAccount } from "@/hooks/useAccounts";
import {
  useCanonicalCaseId,
  usePersistWorkspaceTab,
  useWorkspaceTabQuery,
  useGenerateWorkspaceIntelligence,
} from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// DIL hooks
import { useAccountHypotheses, type ValueHypothesis } from "@/hooks/useHypotheses";
import { useProducts, type Product, type ProductListResponse } from "@/hooks/useProducts";

// ── Types ──────────────────────────────────────────────────────────────────────
interface Recommendation {
  id: string;
  title: string;
  priority: "critical" | "high" | "medium";
  projectedValue: string;
  confidence: "high" | "medium" | "low";
  horizon: string;
  prospectPain: string;
  rootDriver: string;
  ourCapability: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-blue-100 text-blue-700",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  validated: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-600",
  converted: "bg-blue-100 text-blue-700",
};

// ── Hypothesis Card ────────────────────────────────────────────────────────────
function HypothesisCard({ h }: { h: ValueHypothesis }) {
  return (
    <div className="px-3 py-2.5 border border-border rounded-md">
      <div className="flex items-start gap-2">
        <Lightbulb size={13} className="text-amber-500 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-[12px] font-medium leading-snug truncate">
            {h.hypothesis_text}
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className={cn("text-[10px] px-1.5 py-0.5 rounded font-semibold", STATUS_COLORS[h.status] ?? "bg-gray-100 text-gray-600")}>
              {h.status}
            </span>
            <span className="text-[10px] text-muted-foreground">
              {Math.round(h.confidence * 100)}% confidence
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Product Badge ──────────────────────────────────────────────────────────────
function ProductBadge({ p }: { p: Product }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 border border-border rounded-md">
      <Package size={13} className="text-primary shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-medium truncate">{p.name}</p>
        <p className="text-[10px] text-muted-foreground truncate">{p.category}</p>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function ActionPlanTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{
    recommendations: Recommendation[];
  }>(caseId ?? null, "action-plan");
  const persistTab = usePersistWorkspaceTab("action-plan");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  // DIL data
  const { data: hypothesesData } = useAccountHypotheses(accountId ?? null, { status: "validated" });
  const { data: productsData } = useProducts();

  useEffect(() => {
    if (caseId && data) persistTab.mutate({ caseId, payload: data });
  }, [caseId, data]);

  const recommendations = data?.recommendations ?? [];
  const hypotheses = hypothesesData?.hypotheses ?? [];
  const products = (productsData as ProductListResponse | undefined)?.products ?? [];

  const totalValue = useMemo(
    () =>
      recommendations.reduce(
        (sum, rec) => sum + Number((rec.projectedValue || "").replace(/[^\d.-]/g, "")),
        0
      ),
    [recommendations]
  );

  const { messages, sendMessage, suggestedActions } = useAgentStream({
    activeTab: "action-plan",
    accountName: account?.name ?? "Account",
  });

  const generateMutation = useGenerateWorkspaceIntelligence();

  useEffect(() => {
    if (caseId && recommendations.length === 0 && !isLoading && !generateMutation.isPending) {
      generateMutation.mutate(caseId);
    }
  }, [caseId, recommendations.length, isLoading]);

  if (isLoading || generateMutation.isPending)
    return (
      <div className="p-6 text-sm text-muted-foreground">
        {generateMutation.isPending ? "Generating action plan..." : "Loading action plan…"}
      </div>
    );
  if (error || generateMutation.isError || !account)
    return <div className="p-6 text-sm text-destructive">Failed to load action plan.</div>;

  return (
    <ValueStudioShellComponent
      account={{
        accountName: account.name,
        industry: account.industry ?? "Unknown",
        revenue: account.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="action-plan"
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
        />
      }
    >
      {/* Metrics row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard label="Recommendations" value={String(recommendations.length)} />
        <MetricCard label="Total Projected Value" value={`$${totalValue.toLocaleString()}`} />
        <MetricCard
          label="Avg Confidence"
          value={`${Math.round(
            (recommendations.filter((r) => r.confidence === "high").length /
              Math.max(recommendations.length, 1)) *
              100
          )}% high`}
        />
        <MetricCard
          label="Validated Hypotheses"
          value={String(hypotheses.length)}
          trend={hypotheses.length > 0 ? "From DIL engine" : undefined}
        />
      </div>

      {/* DIL Hypotheses Section */}
      {hypotheses.length > 0 && (
        <SectionCard title="Value Hypotheses" className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={13} className="text-amber-500" />
            <span className="text-[11px] text-muted-foreground">
              Generated by the Value Hypothesis Engine — validated signals mapped to product capabilities
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {hypotheses.slice(0, 6).map((h) => (
              <HypothesisCard key={h.id} h={h} />
            ))}
          </div>
          {hypotheses.length > 6 && (
            <p className="text-[10px] text-muted-foreground mt-2">
              +{hypotheses.length - 6} more hypotheses
            </p>
          )}
        </SectionCard>
      )}

      {/* Recommendations (existing workspace data) */}
      {recommendations.length === 0 ? (
        <SectionCard title="Recommendations">
          <div className="text-sm text-muted-foreground">
            No action-plan outputs available for this case yet.
          </div>
        </SectionCard>
      ) : (
        <div className="space-y-3">
          {recommendations.map((rec) => {
            const expanded = expandedId === rec.id;
            return (
              <SectionCard key={rec.id}>
                <button
                  onClick={() => setExpandedId(expanded ? null : rec.id)}
                  className="flex items-start gap-3 w-full text-left"
                >
                  <span
                    className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded font-semibold shrink-0 mt-0.5",
                      PRIORITY_COLORS[rec.priority] ?? "bg-gray-100"
                    )}
                  >
                    {rec.priority}
                  </span>
                  <div className="flex-1">
                    <h3 className="text-[13px] font-bold">{rec.title}</h3>
                    <div className="text-xs text-muted-foreground">
                      {rec.horizon} · {rec.projectedValue}
                    </div>
                  </div>
                  {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {expanded && (
                  <div className="mt-3 text-xs space-y-2 pl-8">
                    <p>
                      <b>Prospect Pain:</b> {rec.prospectPain}
                    </p>
                    <p>
                      <b>Root Driver:</b> {rec.rootDriver}
                    </p>
                    <p>
                      <b>Capability:</b> {rec.ourCapability}
                    </p>
                    <Btn variant="primary">Accept → Value Model</Btn>
                  </div>
                )}
              </SectionCard>
            );
          })}
        </div>
      )}

      {/* Product Portfolio (DIL) */}
      {products.length > 0 && (
        <SectionCard title="Product Portfolio" className="mt-4">
          <p className="text-[11px] text-muted-foreground mb-3">
            Products from the knowledge graph that map to identified capabilities
          </p>
          <div className="grid grid-cols-3 gap-2">
            {products.slice(0, 6).map((p) => (
              <ProductBadge key={p.id} p={p} />
            ))}
          </div>
        </SectionCard>
      )}
    </ValueStudioShellComponent>
  );
}
