import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { FileText, CheckCircle2, AlertCircle, ChevronRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import { useCanonicalCaseId, useEvidenceDecisionMutation, usePersistWorkspaceTab, useValidateEvidenceClaim, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

type VerificationState = "verified" | "partial" | "unverified";
interface EvidenceItem { id: string; title: string; type: string; source: string; matchScore: number; verification: VerificationState; linkedSignals: string[]; excerpt: string; decision_status?: "accepted"|"rejected"|"attached_to_driver"; attached_driver_id?: string }
const VERIFICATION_CONFIG: Record<VerificationState, { icon: typeof CheckCircle2; color: string }> = { verified: { icon: CheckCircle2, color: "text-green-600" }, partial: { icon: AlertCircle, color: "text-orange-600" }, unverified: { icon: AlertCircle, color: "text-muted-foreground" } };

function useEvidenceTabState() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{ evidence: EvidenceItem[] }>(caseId ?? null, "evidence");
  const persistTab = usePersistWorkspaceTab("evidence");
  const validateClaim = useValidateEvidenceClaim();
  const evidenceDecision = useEvidenceDecisionMutation();
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");

  useEffect(() => { if (caseId && data) persistTab.mutate({ caseId, payload: data }); }, [caseId, data]);

  const evidence = data?.evidence ?? [];
  const verified = useMemo(() => evidence.filter((e) => e.verification === "verified").length, [evidence]);
  const avgMatch = evidence.length ? Math.round(evidence.reduce((s, e) => s + e.matchScore, 0) / evidence.length) : 0;

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({ activeTab: "evidence", accountName: account?.name ?? "Account", accountId: accountId ?? undefined });

  return {
    account, accountLoading, caseId, evidence, isLoading, error, verified, avgMatch,
    selectedEvidence, setSelectedEvidence, railMode, setRailMode,
    messages, sendMessage, suggestedActions, steps, isStreaming, metadata,
    validateClaim,
    evidenceDecision,
    persistTab,
    data,
  };
}

export function EvidenceTabContent() {
  const { accountId } = useParams<{ accountId: string }>();
  const {
    evidence, isLoading, error, verified, avgMatch,
    selectedEvidence, setSelectedEvidence,
    caseId, evidenceDecision, persistTab, data,
  } = useEvidenceTabState();

  const [optimisticDecision, setOptimisticDecision] = useState<Record<string, EvidenceItem["decision_status"]>>({});
  const [lastFailedAction, setLastFailedAction] = useState<{ evidenceId: string; decision: "accepted"|"rejected"|"attached_to_driver"; driverId?: string } | null>(null);

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }



  const runDecision = async (evidenceId: string, decision: "accepted"|"rejected"|"attached_to_driver", driverId?: string) => {
    if (!accountId || !caseId) return;
    setOptimisticDecision((prev) => ({ ...prev, [evidenceId]: decision }));
    setLastFailedAction(null);
    try {
      await evidenceDecision.mutateAsync({ evidenceId, accountId, caseId, decision, driverId });
    } catch {
      setOptimisticDecision((prev) => ({ ...prev, [evidenceId]: undefined }));
      setLastFailedAction({ evidenceId, decision, driverId });
    }
  };

  if (isLoading) return <CenteredLoader message="Loading evidence…" />;
  if (error) return <div className="p-6 text-sm text-destructive">Failed to load evidence.</div>;

  return (
    <>
      {persistTab.persistState !== "saved" && (
        <div className="mb-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs flex items-center justify-between">
          <span>{persistTab.persistState === "failed" ? "Could not persist evidence tab." : "Evidence tab has unsaved persistence state."}</span>
          {persistTab.persistState === "failed" && caseId && <Btn variant="outline" className="h-7" onClick={() => persistTab.mutate({ caseId, payload: data ?? { evidence: [] } })}>Retry save</Btn>}
        </div>
      )}
      {evidence.length === 0 ? (
        <SectionCard title="Evidence Library">
          <div className="text-sm text-muted-foreground">No evidence has been returned for this case.</div>
        </SectionCard>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <MetricCard label="Evidence Items" value={String(evidence.length)} trend={`${verified} verified`} />
            <MetricCard label="Avg Match Score" value={`${avgMatch}%`} />
            <MetricCard label="Source Types" value={String(new Set(evidence.map((e) => e.type)).size)} />
          </div>
          <SectionCard title="Evidence Library">
            <div className="space-y-1">
              {evidence.map((item) => {
                const decision = optimisticDecision[item.id] ?? item.decision_status;
                const vc = VERIFICATION_CONFIG[item.verification];
                const Icon = vc.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setSelectedEvidence(item)}
                    className={cn(
                      "flex items-center gap-4 w-full px-3 py-3 rounded-md text-left",
                      selectedEvidence?.id === item.id ? "bg-primary/5" : "hover:bg-muted/50"
                    )}
                  >
                    <FileText size={14} />
                    <div className="flex-1">
                      <div className="text-xs font-medium">{item.title}</div>
                      <div className="text-[10px] text-muted-foreground">{item.linkedSignals.join(" · ")}</div>
                    </div>
                    <span className={cn("flex items-center gap-1 text-[10px] font-semibold", vc.color)}>
                      <Icon size={10} />{item.matchScore}%
                    </span>
                    <span className="text-[10px] text-muted-foreground capitalize">{decision?.replaceAll("_", " ") ?? "pending"}</span><ChevronRight size={12} />
                  </button>
                );
              })}
            </div>
          </SectionCard>
        </>
      )}
      {lastFailedAction && (
        <div className="mt-3 text-xs text-destructive flex items-center gap-2">
          Action failed.
          <Btn variant="outline" className="h-7" onClick={() => runDecision(lastFailedAction.evidenceId, lastFailedAction.decision, lastFailedAction.driverId)}>Retry</Btn>
        </div>
      )}
      {selectedEvidence && (
        <div className="mt-4 flex gap-2">
          <Btn variant="primary" className="h-8" onClick={() => runDecision(selectedEvidence.id, "accepted")} disabled={evidenceDecision.isPending}>Accept</Btn>
          <Btn variant="outline" className="h-8" onClick={() => runDecision(selectedEvidence.id, "rejected")} disabled={evidenceDecision.isPending}>Reject</Btn>
          <Btn variant="ghost" className="h-8" onClick={() => runDecision(selectedEvidence.id, "attached_to_driver", "driver-auto")} disabled={evidenceDecision.isPending}>Attach to driver</Btn>
        </div>
      )}
    </>
  );
}

export default function EvidenceTab() {
  const {
    account, accountLoading, selectedEvidence, railMode, setRailMode,
    messages, sendMessage, suggestedActions, steps, isStreaming, metadata,
  } = useEvidenceTabState();

  const { accountId } = useParams<{ accountId: string }>();

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <CenteredLoader message="Loading evidence…" />;
  }

  if (!account) {
    return <div className="p-6 text-sm text-destructive">Account not found.</div>;
  }

  return (
    <IntelligenceShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="evidence"
          detailContent={
            selectedEvidence ? (
              <div className="space-y-2">
                <h3 className="text-sm font-bold">{selectedEvidence.title}</h3>
                <p className="text-xs text-muted-foreground">{selectedEvidence.excerpt}</p>
              </div>
            ) : null
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
      <EvidenceTabContent />
    </IntelligenceShell>
  );
}
