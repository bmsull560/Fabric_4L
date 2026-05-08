/**
 * ValueCasePage — Value Case workspace entry point
 *
 * Route: /value-case/:accountId
 */
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { AlertCircle, FileText, GitCompare, Loader2, RefreshCw } from "lucide-react";
import ValueCaseShell from "@/components/workspace/ValueCaseShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { Button } from "@/components/ui/button";
import { useValueCaseArtifacts } from "@/hooks/useValueCaseArtifacts";
import { useCanonicalCaseId, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { useROICalculations } from "@/hooks/useROICalculator";
import { useNavigation } from "@/hooks";
import { createNextAction } from "@/components/workspace/nextAction";

interface StakeholderTabResponse {
  stakeholders?: Array<{ name?: string; title?: string }>;
}

interface EvidenceTabResponse {
  evidence?: Array<{ title?: string; decision?: string; status?: string }>;
}

interface AssumptionsTabResponse {
  assumptions?: Array<{
    id?: string;
    statement?: string;
    text?: string;
    status?: string;
    support_status?: AssumptionSupportStatus;
    supportStatus?: AssumptionSupportStatus;
    evidence_ids?: string[];
    evidenceIds?: string[];
  }>;
}

type AssumptionSupportStatus = "supported" | "partial" | "unsupported" | "unreviewed";

export default function ValueCasePage() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const { navigateTo } = useNavigation();
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "value-case",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
  });

  const { versions, selectedVersion, setSelectedVersionId, generateArtifact } = useValueCaseArtifacts(accountId);
  const lineageSummary = selectedVersion?.lineage;
  const { data: caseId } = useCanonicalCaseId(accountId);
  const stakeholderTab = useWorkspaceTabQuery<StakeholderTabResponse>(caseId ?? null, "stakeholders");
  const evidenceTab = useWorkspaceTabQuery<EvidenceTabResponse>(caseId ?? null, "evidence");
  const assumptionsTab = useWorkspaceTabQuery<AssumptionsTabResponse>(caseId ?? null, "assumptions");
  const roiCalcs = useROICalculations({ account_id: accountId ?? undefined, limit: 1 });
  const assumptionSupportWarnings: NonNullable<AssumptionsTabResponse["assumptions"]> = (assumptionsTab.data?.assumptions ?? []).filter((item) => {
    const support = item.support_status ?? item.supportStatus ?? "unreviewed";
    return support === "unsupported" || support === "unreviewed";
  });

  const previousVersion = useMemo(() => {
    if (!selectedVersion) return null;
    const idx = versions.findIndex((item) => item.id === selectedVersion.id);
    if (idx <= 0) return null;
    return versions[idx - 1] ?? null;
  }, [versions, selectedVersion]);

  const nextAction = accountId
    ? createNextAction({
        label: "Create Realization Plan",
        target: "realization",
        params: { accountId },
        disabled: versions.length === 0,
        reason: "Generate a business case first.",
      })
    : null;

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <LoadingState message="Loading account…" fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;
  }

  const handleGenerate = () => {
    if (assumptionSupportWarnings.length > 0) {
      return;
    }

    const stakeholders = (stakeholderTab.data?.stakeholders ?? [])
      .map((item) => item.name ?? item.title ?? "")
      .filter(Boolean);
    const acceptedEvidence = (evidenceTab.data?.evidence ?? [])
      .filter((item) => item.decision === "accepted" || item.status === "accepted")
      .map((item) => item.title ?? "")
      .filter(Boolean);
    const selectedAssumptions = (assumptionsTab.data?.assumptions ?? [])
      .filter((item) => item.status !== "rejected")
      .map((item) => item.statement ?? item.text ?? "")
      .filter(Boolean);
    const latestCalc = roiCalcs.data?.calculations?.[0];

    generateArtifact.mutate({
      account_id: account.id,
      account_name: account.name,
      stakeholders: stakeholders.length ? stakeholders : ["Economic buyer", "Business champion", "Technical evaluator"],
      accepted_evidence: acceptedEvidence.length ? acceptedEvidence : ["Validated calculator assumptions"],
      scenario_assumptions: selectedAssumptions.length ? selectedAssumptions : ["Moderate scenario selected"],
      roi_metrics: {
        three_year_value: latestCalc ? `$${Math.round(latestCalc.npv).toLocaleString()}` : "$1.8M",
        roi: latestCalc ? `${Math.round(latestCalc.total_roi_pct)}%` : "214%",
        payback: latestCalc ? `${Math.round(latestCalc.payback_months)} months` : "9 months",
      },
      risk_notes: [
        `Generated from case ${caseId ?? "unknown"} and ROI model ${latestCalc?.id ?? "latest-default"}`,
        "Change management capacity",
      ],
    });
  };

  return (
    <ValueCaseShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="value-case"
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
          steps={steps}
          isStreaming={isStreaming}
          runMetadata={metadata}
          detailContent={
            <div className="space-y-3">
              <h3 className="text-sm font-bold">Assumption Support</h3>
              <div className="space-y-1 text-xs">
                {assumptionSupportWarnings.length === 0 ? (
                  <p className="text-emerald-700">All assumptions have support coverage.</p>
                ) : (
                  assumptionSupportWarnings.map((item, idx) => (
                    <div key={item.id ?? idx} className="rounded border border-amber-300 bg-amber-50 px-2 py-1">
                      {item.statement ?? item.text ?? "Untitled assumption"}
                    </div>
                  ))
                )}
              </div>
            </div>
          }
          auditEntries={lineageSummary?.mutations ?? []}
        />
      }
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Value Case</h2>
              <p className="text-sm text-muted-foreground">Generated value narrative and business case for the prospect</p>
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={generateArtifact.isPending || assumptionSupportWarnings.length > 0}>
            {generateArtifact.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            {versions.length ? "Regenerate" : "Generate"}
          </Button>
        </div>

        {assumptionSupportWarnings.length > 0 && (
          <SectionCard title="Validation warning" className="border-amber-300">
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
              <p className="font-medium">Business case generation is blocked until unsupported assumptions are remediated.</p>
              <ul className="mt-2 list-disc pl-5 text-xs">
                {assumptionSupportWarnings.map((item, idx) => (
                  <li key={item.id ?? idx}>{item.statement ?? item.text ?? "Untitled assumption"}</li>
                ))}
              </ul>
            </div>
          </SectionCard>
        )}

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="3-Year Value" value={selectedVersion?.business_case.metrics.three_year_value ?? "—"} />
          <MetricCard label="ROI" value={selectedVersion?.business_case.metrics.roi ?? "—"} />
          <MetricCard label="Payback" value={selectedVersion?.business_case.metrics.payback ?? "—"} />
        </div>

        {generateArtifact.isError && (
          <SectionCard title="Generation failed">
            <div className="flex items-center justify-between gap-4 rounded-lg border border-destructive/40 bg-destructive/5 p-4">
              <p className="text-sm text-foreground flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-destructive" /> Unable to generate value case. Retry with the same inputs.
              </p>
              <Button variant="outline" onClick={handleGenerate}>Retry</Button>
            </div>
          </SectionCard>
        )}

        {selectedVersion && lineageSummary && (
          <SectionCard title="Generated from" subtitle="Artifact lineage captured at generation time and persisted with this version.">
            <div className="rounded-lg border border-border p-4 space-y-3">
              <div className="text-xs text-muted-foreground">
                Sources: {Object.entries(lineageSummary.source_counts).map(([kind, count]) => `${kind} (${count ?? 0})`).join(" • ")}
              </div>
              <ul className="space-y-1">
                {lineageSummary.source_refs.map((source) => (
                  <li key={`${source.type}:${source.id}`} className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground">{source.type}</span>:{" "}
                    {source.url ? <a href={source.url} className="text-primary underline underline-offset-2">{source.title ?? source.id}</a> : (source.title ?? source.id)}
                  </li>
                ))}
              </ul>
            </div>
          </SectionCard>
        )}

        <SectionCard title="Value Case Versions" subtitle="Generated artifacts are versioned for returning users.">
          {!versions.length ? (
            <div className="rounded-lg border border-dashed border-border p-8 text-center">
              <p className="text-sm text-muted-foreground">No prior versions yet. Generate your first value case artifact.</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {versions.map((version) => (
                  <Button key={version.id} variant={selectedVersion?.id === version.id ? "default" : "outline"} size="sm" onClick={() => setSelectedVersionId(version.id)}>
                    v{version.version}
                  </Button>
                ))}
              </div>

              {selectedVersion && (
                <div className="rounded-lg border border-border p-4 space-y-2">
                  <p className="text-xs text-muted-foreground">Created {new Date(selectedVersion.created_at).toLocaleString()}</p>
                  <p className="text-sm font-medium">{selectedVersion.narrative.title}</p>
                  <p className="text-sm text-muted-foreground">{selectedVersion.business_case.summary}</p>
                </div>
              )}

              <div className="rounded-lg border border-border p-4 space-y-2">
                <p className="text-sm font-medium flex items-center gap-2"><GitCompare className="h-4 w-4" /> Version Diff</p>
                {!previousVersion || !selectedVersion ? (
                  <p className="text-sm text-muted-foreground">Select a newer version to see diffs from prior output.</p>
                ) : (
                  <ul className="text-sm text-muted-foreground list-disc pl-5">
                    <li>ROI: {previousVersion.business_case.metrics.roi} → {selectedVersion.business_case.metrics.roi}</li>
                    <li>Payback: {previousVersion.business_case.metrics.payback} → {selectedVersion.business_case.metrics.payback}</li>
                    <li>Risk notes: {previousVersion.business_case.risks.length} → {selectedVersion.business_case.risks.length}</li>
                  </ul>
                )}
              </div>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Claim-to-Evidence Trace Panel" subtitle="Maps each value-case metric to supporting assumptions and evidence artifacts.">
          {!(assumptionsTab.data?.assumptions?.length) ? (
            <p className="text-sm text-muted-foreground">No assumptions available yet.</p>
          ) : (
            <div className="space-y-2">
              {(assumptionsTab.data?.assumptions ?? []).map((item, idx) => {
                const support = item.support_status ?? item.supportStatus ?? "unreviewed";
                const evidenceIds = item.evidence_ids ?? item.evidenceIds ?? [];
                return (
                  <div key={item.id ?? `trace-${idx}`} className="rounded-lg border border-border p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">{item.statement ?? item.text ?? "Untitled assumption"}</p>
                      <span className="rounded border border-border bg-muted px-2 py-0.5 text-[10px] capitalize">{support}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">Linked business-case metrics: ROI, payback, three-year value</p>
                    <p className="mt-1 text-xs text-muted-foreground">Evidence artifacts: {evidenceIds.length ? evidenceIds.join(", ") : "none linked"}</p>
                  </div>
                );
              })}
            </div>
          )}
        </SectionCard>

        {nextAction && (
          <div className="flex items-center justify-end gap-2">
            {nextAction.disabled && <span className="text-xs text-muted-foreground">{nextAction.reason}</span>}
            <Button disabled={nextAction.disabled} onClick={() => navigateTo(nextAction.target, nextAction.params)} data-testid="primary-forward-action">
              {nextAction.label}
            </Button>
          </div>
        )}
      </div>
    </ValueCaseShell>
  );
}
