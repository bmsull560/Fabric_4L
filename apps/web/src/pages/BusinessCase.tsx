/**
 * Screen 9 — Business Case Viewer
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { Download, Share2, AlertCircle, Loader2, Sparkles, RefreshCw, CheckCircle2, FileText, Send, TrendingUp } from "lucide-react";
import { useParams, useSearchParams } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { GateStatusBanner } from "@/components/GateStatusBanner";
import { useBusinessCase, useBusinessCaseExport, useRegenerateBusinessCase } from "@/hooks/useDocuments";
import { useNavigation } from "@/hooks";
import { SectionCard } from "@/components/blocks/SectionCard";
import { PageHeader, Btn } from "@/components/ui/fabric";
import { cn } from "@/lib/utils";
import type { ValidationState } from "@/api/harness";

function metadataString(metadata: Record<string, unknown> | undefined, keys: string[]): string {
  for (const key of keys) {
    const value = metadata?.[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return "";
}

function metadataBoolean(metadata: Record<string, unknown> | undefined, keys: string[]): boolean {
  return keys.some((key) => metadata?.[key] === true);
}

// ── Validation badge helpers ──────────────────────────────────────────────────

function validationBadgeClass(state: ValidationState): string {
  switch (state) {
    case "passed":               return "bg-emerald-500/15 text-emerald-700 border-emerald-200";
    case "failed":               return "bg-red-500/15 text-red-700 border-red-200";
    case "needs_review":         return "bg-amber-500/15 text-amber-700 border-amber-200";
    case "insufficient_evidence": return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function validationBadgeLabel(state: ValidationState): string {
  switch (state) {
    case "passed":               return "Validated";
    case "failed":               return "Blocked";
    case "needs_review":         return "Needs Review";
    case "insufficient_evidence": return "Insufficient Evidence";
  }
}

/** Derive an overall ValidationState from a validation_summary object in case_metadata. */
function deriveOverallValidationState(
  summary: Record<string, unknown> | undefined,
): ValidationState | null {
  if (!summary || typeof summary.total !== "number" || summary.total === 0) return null;
  if ((summary.failed as number) > 0) return "failed";
  if ((summary.needs_review as number) > 0 || (summary.insufficient_evidence as number) > 0)
    return "needs_review";
  if ((summary.passed as number) === summary.total) return "passed";
  return "insufficient_evidence";
}

/** Return the ValidationState for a claim at a given recommendation index. */
function claimValidationState(
  claimValidations: unknown,
  index: number,
): ValidationState | null {
  if (!Array.isArray(claimValidations)) return null;
  const entry = claimValidations[index];
  if (!entry || typeof entry !== "object") return null;
  const state = (entry as Record<string, unknown>).validation_state as string | undefined;
  const validStates: ValidationState[] = ["passed", "failed", "needs_review", "insufficient_evidence"];
  return validStates.includes(state as ValidationState) ? (state as ValidationState) : null;
}

export default function BusinessCase() {
  const { caseId } = useParams<{ caseId: string }>();
  const [searchParams] = useSearchParams();
  const { navigateTo } = useNavigation();
  const businessCaseId = caseId ?? searchParams.get("id");

  const { data: businessCase, isLoading, error } = useBusinessCase(businessCaseId);
  const exportMutation = useBusinessCaseExport();
  const regenerateMutation = useRegenerateBusinessCase();

  // Handle missing ID gracefully
  if (!businessCaseId) {
    return (
      <div className="p-6 max-w-5xl">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-700">
          No business case ID provided. Please select a business case to view.
        </div>
      </div>
    );
  }

  const handleExportPDF = () => {
    if (!businessCase || !businessCaseId) return;
    exportMutation.mutate({
      caseId: businessCaseId,
      format: "pdf",
    });
  };

  const handleViewTrace = () => {
    // Navigate to DecisionTrace
    if (businessCaseId) {
      navigateTo('decision-trace', undefined, { query: { caseId: businessCaseId } });
    }
  };

  const handleExploreInteractive = () => {
    // Navigate to Interactive Business Case explorer
    if (businessCaseId) {
      navigateTo('business-case-interactive', undefined, { query: { id: businessCaseId } });
    }
  };
  const handleRegenerate = () => {
    if (!businessCaseId) return;
    const accountId = String(businessCase?.case_metadata?.account_id ?? "");
    if (!accountId) return;
    regenerateMutation.mutate({ caseId: businessCaseId, accountId });
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl">
        {/* Header skeleton */}
        <div className="mb-5">
          <Skeleton className="h-4 w-48 mb-2" />
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <Skeleton className="h-8 w-64 mb-1" />
              <Skeleton className="h-4 w-48" />
            </div>
            <div className="flex items-center gap-2">
              <Skeleton className="h-8 w-28" />
              <Skeleton className="h-8 w-28" />
            </div>
          </div>
        </div>

        {/* Hero ROI card skeleton */}
        <div className="rounded-xl p-6 mb-6 bg-gradient-to-br from-blue-700/20 to-blue-900/20 border border-blue-200">
          <Skeleton className="h-3 w-32 mb-1" />
          <Skeleton className="h-12 w-48 mb-1" />
          <Skeleton className="h-4 w-64 mb-4" />
          <div className="flex gap-6">
            <div>
              <Skeleton className="h-3 w-16 mb-1" />
              <Skeleton className="h-6 w-12" />
            </div>
            <div>
              <Skeleton className="h-3 w-24 mb-1" />
              <Skeleton className="h-6 w-20" />
            </div>
            <div>
              <Skeleton className="h-3 w-12 mb-1" />
              <Skeleton className="h-6 w-8" />
            </div>
          </div>
        </div>

        {/* Recommendations skeleton */}
        <SectionCard title="Recommendations" className="mb-5">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start gap-2">
                <Skeleton className="h-4 w-4 shrink-0" />
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        </SectionCard>

        {/* Executive Summary skeleton */}
        <SectionCard title="Executive Summary">
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-full" />
          </div>
        </SectionCard>
      </div>
    );
  }

  if (error || !businessCase) {
    return (
      <div className="p-6 max-w-5xl">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error instanceof Error ? error.message : 'Failed to load business case. Please try again.'}</span>
          </div>
        </div>
      </div>
    );
  }

  const normalizedStatus = businessCase.status.toLowerCase();
  const isApproved = ["approved", "active", "completed"].includes(normalizedStatus);
  const hasExportDocument = Boolean(businessCase.document_url);
  const exportState = isApproved && hasExportDocument ? "Export PDF ready" : "Export PDF disabled until approval and document generation complete";
  const accountRouteId =
    metadataString(businessCase.case_metadata, ["external_account_id", "provider_record_id", "account_route_id"]) ||
    metadataString(businessCase.case_metadata, ["account_id"]);
  const crmReady = isApproved && metadataBoolean(businessCase.case_metadata, [
    "crm_push_ready",
    "crm_push_available",
    "crm_sync_ready",
  ]);
  const realizationReady = isApproved && metadataBoolean(businessCase.case_metadata, [
    "realization_conversion_ready",
    "realization_conversion_available",
    "post_sale_realization_ready",
  ]);

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={[{ label: "Agent Workflows" }, { label: "Business Cases" }]}
        title={businessCase.title || "Business Case"}
        subtitle={`Status: ${businessCase.status} · ${businessCase.created_at ? new Date(businessCase.created_at).toLocaleDateString() : 'Unknown'}`}
        actions={
          <>
            <Btn
              variant="ghost"
              onClick={handleExploreInteractive}
              className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
            >
              <Sparkles size={12} className="mr-1" />
              Explore
            </Btn>
            <Btn
              variant="ghost"
              onClick={handleExportPDF}
              disabled={exportMutation.isPending || !businessCase.document_url}
            >
              {exportMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
              Export PDF
            </Btn>
            <Btn variant="ghost" onClick={handleViewTrace}><Share2 size={12}/> View Trace</Btn>
            <Btn variant="ghost" onClick={handleRegenerate} disabled={regenerateMutation.isPending || !businessCase?.case_metadata?.account_id}>
              {regenerateMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
              Regenerate Business Case
            </Btn>
          </>
        }
      />

      {accountRouteId && <GateStatusBanner accountId={accountRouteId} />}

      {/* Export error */}
      {exportMutation.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 flex items-center gap-2 text-red-700 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{exportMutation.error.message}</span>
        </div>
      )}

      <SectionCard title="Business Case Lifecycle" className="mb-5">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-border bg-card p-3">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <FileText size={13} />
              Business Case
            </div>
            <p className="mt-2 text-[13px] text-foreground">{businessCase.case_id}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-3">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <CheckCircle2 size={13} />
              Approval Status
            </div>
            <p className="mt-2 text-[13px] font-semibold text-foreground">{isApproved ? "Approved" : "Draft"}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-3">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <CheckCircle2 size={13} />
              Claim Validation
            </div>
            <div className="mt-2">
              {(() => {
                const overallState = deriveOverallValidationState(
                  businessCase.case_metadata?.validation_summary as Record<string, unknown> | undefined
                );
                return overallState ? (
                  <Badge
                    variant="outline"
                    className={cn("text-[11px]", validationBadgeClass(overallState))}
                  >
                    {validationBadgeLabel(overallState)}
                  </Badge>
                ) : (
                  <p className="text-[13px] text-muted-foreground">Not validated</p>
                );
              })()}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-3">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              <Download size={13} />
              Export Gate
            </div>
            <p className="mt-2 text-[13px] text-foreground">{exportState}</p>
          </div>
        </div>
      </SectionCard>

      {/* Hero ROI card */}
      <div className="bg-gradient-to-br from-blue-700 to-blue-900 rounded-xl p-6 mb-6 text-white shadow-lg">
        <div className="text-[11px] font-bold uppercase tracking-wider opacity-70 mb-1">Total Estimated Value</div>
        <div className="text-[48px] font-extrabold leading-none mb-1">
          ${businessCase.total_value.toLocaleString()}
        </div>
        <div className="text-[13px] opacity-80">
          ROI Ratio: {businessCase.roi_ratio.toFixed(2)}x · Payback: {businessCase.payback_months} months
        </div>
        <div className="flex gap-6 mt-4">
          <div>
            <div className="text-[10px] uppercase tracking-wider opacity-60">Confidence</div>
            <div className="text-[18px] font-bold">{Math.round(businessCase.confidence_score * 100)}%</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider opacity-60">Implementation Cost</div>
            <div className="text-[18px] font-bold">${businessCase.implementation_cost.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider opacity-60">Pages</div>
            <div className="text-[18px] font-bold">{businessCase.page_count}</div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {businessCase.recommendations?.length > 0 && (
        <SectionCard title="Recommendations" className="mb-5">
          <ul className="space-y-2">
            {businessCase.recommendations.map((rec, idx) => {
              const claimState = claimValidationState(
                businessCase.case_metadata?.claim_validations,
                idx,
              );
              return (
                <li key={idx} className="flex items-start gap-2 text-[13px] text-neutral-700">
                  <span className="text-blue-600 font-bold shrink-0">{idx + 1}.</span>
                  <span className="flex-1">{rec}</span>
                  {claimState && (
                    <Badge
                      variant="outline"
                      className={cn("text-[10px] shrink-0 self-start mt-0.5", validationBadgeClass(claimState))}
                    >
                      {validationBadgeLabel(claimState)}
                    </Badge>
                  )}
                </li>
              );
            })}
          </ul>
        </SectionCard>
      )}

      {/* Executive Summary */}
      <SectionCard title="Executive Summary">
        <div className="prose prose-sm max-w-none text-neutral-700 text-[13px] leading-relaxed whitespace-pre-wrap">
          {businessCase.summary}
        </div>
      </SectionCard>
      <SectionCard title="Post-Approval Actions" className="mt-5">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2 text-[12px] font-semibold text-foreground">
              <Send size={14} />
              CRM Push
            </div>
            <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
              {crmReady
                ? "Approved case is ready to push to CRM as a renewal or expansion proof package."
                : "CRM push is held until the business case is approved and export metadata is ready."}
            </p>
            <Btn variant="ghost" className="mt-3" disabled={!crmReady}>
              Push to CRM
            </Btn>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-center gap-2 text-[12px] font-semibold text-foreground">
              <TrendingUp size={14} />
              Value Realization
            </div>
            <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">
              {realizationReady
                ? "Convert this approved business case into post-sale realization tracking for baseline, actuals, outcomes, and renewal narrative."
                : "Realization conversion becomes available after approval and case handoff metadata are ready."}
            </p>
            <Btn
              variant="ghost"
              className="mt-3"
              disabled={!realizationReady || !accountRouteId}
              onClick={() => accountRouteId && navigateTo("realization", { accountId: accountRouteId })}
            >
              Convert to Value Realization
            </Btn>
          </div>
        </div>
      </SectionCard>
      {/* Claim Traceability — evidence, benchmarks, assumptions */}
      {businessCase.truth_references && businessCase.truth_references.length > 0 && (
        <SectionCard title="Claim Traceability" className="mt-5">
          <p className="text-[11px] text-muted-foreground mb-3">
            Every claim in this business case is traceable to a source: evidence, benchmark, or assumption.
          </p>
          <ul className="space-y-2">
            {businessCase.truth_references.map((ref, idx) => {
              const r = ref as Record<string, unknown>;
              const refType = String(r.type ?? 'reference');
              const typeLabel = refType === 'evidence' ? 'Evidence' : refType === 'benchmark' ? 'Benchmark' : 'Assumption';
              return (
                <li key={idx} className="flex items-start gap-2 text-[12px] border-l-2 border-primary/30 pl-3">
                  <span className="font-semibold text-primary shrink-0">{typeLabel}:</span>
                  <span className="text-foreground">{String(r.claim ?? r.text ?? '')}</span>
                  {r.source != null && (
                    <span className="text-muted-foreground ml-auto shrink-0">— {String(r.source)}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </SectionCard>
      )}
      {businessCase.diff_summary && (
        <SectionCard title="Regeneration Diff Summary" className="mt-5">
          <pre className="text-[12px] whitespace-pre-wrap">{JSON.stringify(businessCase.diff_summary, null, 2)}</pre>
        </SectionCard>
      )}
      {businessCase.revision_history && businessCase.revision_history.length > 0 && (
        <SectionCard title="Revision History" className="mt-5">
          <ul className="space-y-1 text-[12px]">
            {businessCase.revision_history.map((entry, idx) => (
              <li key={idx}>{String(entry.case_id)} · {String(entry.created_at ?? "unknown")}</li>
            ))}
          </ul>
        </SectionCard>
      )}
    </div>
  );
}
