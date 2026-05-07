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

interface StakeholderTabResponse {
  stakeholders?: Array<{ name?: string; title?: string }>;
}
interface EvidenceTabResponse {
  evidence?: Array<{ title?: string; decision?: string; status?: string }>;
}
interface AssumptionsTabResponse {
  assumptions?: Array<{ statement?: string; text?: string; status?: string }>;
}

export default function ValueCasePage() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "value-case",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
  });

  const { versions, selectedVersion, setSelectedVersionId, generateArtifact } = useValueCaseArtifacts(accountId);
  const { data: caseId } = useCanonicalCaseId(accountId);
  const stakeholderTab = useWorkspaceTabQuery<StakeholderTabResponse>(caseId ?? null, "stakeholders");
  const evidenceTab = useWorkspaceTabQuery<EvidenceTabResponse>(caseId ?? null, "evidence");
  const assumptionsTab = useWorkspaceTabQuery<AssumptionsTabResponse>(caseId ?? null, "assumptions");
  const roiCalcs = useROICalculations({ account_id: accountId ?? undefined, limit: 1 });

  const previousVersion = useMemo(() => {
    if (!selectedVersion) return null;
    const idx = versions.findIndex((item) => item.id === selectedVersion.id);
    if (idx <= 0) return null;
    return versions[idx - 1] ?? null;
  }, [versions, selectedVersion]);

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
          <Button onClick={handleGenerate} disabled={generateArtifact.isPending}>
            {generateArtifact.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            {versions.length ? "Regenerate" : "Generate"}
          </Button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="3-Year Value" value={selectedVersion?.business_case.metrics.three_year_value ?? "—"} />
          <MetricCard label="ROI" value={selectedVersion?.business_case.metrics.roi ?? "—"} />
          <MetricCard label="Payback" value={selectedVersion?.business_case.metrics.payback ?? "—"} />
        </div>

        {generateArtifact.isError && (
          <SectionCard title="Generation failed">
            <div className="flex items-center justify-between gap-4 rounded-lg border border-destructive/40 bg-destructive/5 p-4">
              <p className="text-sm text-foreground flex items-center gap-2"><AlertCircle className="h-4 w-4 text-destructive" /> Unable to generate value case. Retry with the same inputs.</p>
              <Button variant="outline" onClick={handleGenerate}>Retry</Button>
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
      </div>
    </ValueCaseShell>
  );
}
