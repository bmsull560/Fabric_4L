import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { FileText, CheckCircle2, AlertCircle, ChevronRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import { useCaseStudies, useLinkEvidence, useUnlinkEvidence, type CaseStudy } from "@/hooks/useEvidence";
import { useCanonicalCaseId, useEvidenceDecisionMutation, usePersistWorkspaceTab, useValidateEvidenceClaim, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

type VerificationState = "verified" | "partial" | "unverified";

interface EvidenceItem {
  id: string;
  title: string;
  type: string;
  source: string;
  matchScore: number;
  verification: VerificationState;
  linkedSignals: string[];
  excerpt: string;
  decision_status?: "accepted" | "rejected" | "attached_to_driver";
  attached_driver_id?: string;
  provenance_id?: string;
  confidence?: number;
  decision_note?: string;
}

interface DriverOption {
  id: string;
  name?: string;
  hypothesis_text?: string;
}

interface EvidenceLink {
  evidence_id: string;
  evidence_title: string;
  driver_id: string;
  linked_at: string;
}

const VERIFICATION_CONFIG: Record<
  VerificationState,
  { icon: typeof CheckCircle2; color: string }
> = {
  verified: { icon: CheckCircle2, color: "text-green-600" },
  partial: { icon: AlertCircle, color: "text-orange-600" },
  unverified: { icon: AlertCircle, color: "text-muted-foreground" },
};

function mapCaseStudyToEvidenceItem(cs: CaseStudy): EvidenceItem {
  const outcomes = cs.outcomes ?? [];
  const avgImprovement =
    outcomes.length > 0
      ? Math.round(
          outcomes.reduce((sum, o) => sum + (o.improvement_pct ?? 0), 0) /
            outcomes.length
        )
      : 0;
  const matchScore = Math.min(100, Math.max(50, 60 + avgImprovement));

  let verification: VerificationState = "unverified";
  if (outcomes.length > 0 && cs.published_date) {
    verification = "verified";
  } else if (outcomes.length > 0 || cs.published_date) {
    verification = "partial";
  }

  return {
    id: cs.id,
    title: cs.title,
    type: cs.evidence_type ?? "case_study",
    source: cs.company_name ?? "Unknown",
    matchScore,
    verification,
    linkedSignals: cs.pain_signals_addressed ?? [],
    excerpt:
      cs.summary ??
      (cs.content ? cs.content.slice(0, 200) + (cs.content.length > 200 ? "…" : "") : "No summary available."),
  };
}

function useEvidenceTabState() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data: driverData } = useWorkspaceTabQuery<{ drivers?: DriverOption[] }>(caseId ?? null, "drivers");
  const { data: linkData } = useWorkspaceTabQuery<{ evidence_links?: EvidenceLink[] }>(caseId ?? null, "evidence-links");
  const persistLinks = usePersistWorkspaceTab("evidence-links");

  const { data, isLoading, error } = useWorkspaceTabQuery<{ evidence: EvidenceItem[] }>(caseId ?? null, "evidence");
  const persistTab = usePersistWorkspaceTab("evidence");
  const validateClaim = useValidateEvidenceClaim();
  const evidenceDecision = useEvidenceDecisionMutation();

  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [selectedDriverId, setSelectedDriverId] = useState("");
  const [railMode, setRailMode] = useState<RightRailMode>("detail");
  const evidenceLinks = linkData?.evidence_links ?? [];
  const driverOptions = driverData?.drivers ?? [];

  const linkMutation = useLinkEvidence();
  const unlinkMutation = useUnlinkEvidence();

  const evidence = useMemo(() => data?.evidence ?? [], [data]);

  const verified = useMemo(
    () => evidence.filter((e) => e.verification === "verified").length,
    [evidence]
  );
  const avgMatch = evidence.length
    ? Math.round(evidence.reduce((s, e) => s + e.matchScore, 0) / evidence.length)
    : 0;

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } =
    useAgentEvents({
      activeTab: "evidence",
      accountName: account?.name ?? "Account",
      accountId: accountId ?? undefined,
      selectedEvidenceId: selectedEvidence?.id,
      workspaceCaseId: caseId ?? undefined,
      entityContext: { selectedEvidence: selectedEvidence ?? undefined },
    });

  const attachEvidence = () => {
    if (!caseId || !selectedEvidence || !selectedDriverId) return;
    const nextLinks = [
      ...evidenceLinks.filter((link) => !(link.evidence_id === selectedEvidence.id && link.driver_id === selectedDriverId)),
      {
        evidence_id: selectedEvidence.id,
        evidence_title: selectedEvidence.title,
        driver_id: selectedDriverId,
        linked_at: new Date().toISOString(),
      },
    ];
    persistLinks.mutate({ caseId, payload: { evidence_links: nextLinks } });
    linkMutation.mutate({ evidence_id: selectedEvidence.id, driver_id: selectedDriverId });
  };

  const unlinkEvidence = (link: EvidenceLink) => {
    if (!caseId) return;
    persistLinks.mutate({
      caseId,
      payload: {
        evidence_links: evidenceLinks.filter((item) =>
          !(item.evidence_id === link.evidence_id && item.driver_id === link.driver_id),
        ),
      },
    });
    unlinkMutation.mutate({ evidence_id: link.evidence_id, driver_id: link.driver_id });
  };

  return {
    account,
    accountLoading,
    caseId,
    evidence,
    isLoading,
    error,
    verified,
    avgMatch,
    selectedEvidence,
    setSelectedEvidence,
    selectedDriverId,
    setSelectedDriverId,
    driverOptions,
    evidenceLinks,
    attachEvidence,
    unlinkEvidence,
    isAttachingEvidence: persistLinks.isPending || linkMutation.isPending,
    railMode,
    setRailMode,
    messages,
    sendMessage,
    suggestedActions,
    steps,
    isStreaming,
    metadata,
    validateClaim,
    evidenceDecision,
    persistTab,
    data,
  };
}

type EvidenceTabState = ReturnType<typeof useEvidenceTabState>;

export function EvidenceTabContent({ state: providedState }: { state?: EvidenceTabState } = {}) {
  const { accountId } = useParams<{ accountId: string }>();
  const ownedState = useEvidenceTabState();
  const {
    evidence,
    isLoading,
    error,
    verified,
    avgMatch,
    selectedEvidence,
    setSelectedEvidence,
    caseId,
    evidenceDecision,
    persistTab,
    data,
  } = providedState ?? ownedState;

  const [optimisticDecision, setOptimisticDecision] = useState<Record<string, EvidenceItem["decision_status"]>>({});
  const [modifyNote, setModifyNote] = useState("");
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
          <div className="text-sm text-muted-foreground">
            No evidence found for this account's industry. Try importing case studies or broadening filters.
          </div>
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
                      <div className="text-[10px] text-muted-foreground">
                        {item.linkedSignals.join(" · ")}
                      </div>
                    </div>
                    <span className={cn("flex items-center gap-1 text-[10px] font-semibold", vc.color)}>
                      <Icon size={10} />
                      {item.matchScore}%
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
        <div className="mt-4 space-y-2">
          <div className="rounded-md border border-border px-3 py-2 text-xs space-y-1">
            <div><span className="font-semibold">Source:</span> {selectedEvidence.source}</div>
            <div><span className="font-semibold">Provenance ID:</span> {selectedEvidence.provenance_id ?? "N/A"}</div>
            <div><span className="font-semibold">Confidence:</span> {typeof selectedEvidence.confidence === "number" ? `${Math.round(selectedEvidence.confidence * 100)}%` : "N/A"}</div>
          </div>
          <div className="flex gap-2">
          <Btn variant="primary" className="h-8" onClick={() => runDecision(selectedEvidence.id, "accepted")} disabled={evidenceDecision.isPending}>Accept</Btn>
          <Btn variant="outline" className="h-8" onClick={() => runDecision(selectedEvidence.id, "rejected")} disabled={evidenceDecision.isPending}>Reject</Btn>
          <Btn variant="ghost" className="h-8" onClick={() => runDecision(selectedEvidence.id, "attached_to_driver", "driver-auto")} disabled={evidenceDecision.isPending}>Modify</Btn>
          </div>
          <input
            value={modifyNote}
            onChange={(e) => setModifyNote(e.target.value)}
            className="w-full border border-border rounded-md px-2 py-1 text-xs"
            placeholder="Optional modification note"
          />
        </div>
      )}
    </>
  );
}

export default function EvidenceTab() {
  const {
    account,
    accountLoading,
    evidence,
    isLoading,
    error,
    verified,
    avgMatch,
    selectedEvidence,
    setSelectedEvidence,
    railMode,
    setRailMode,
    selectedDriverId,
    setSelectedDriverId,
    driverOptions,
    evidenceLinks,
    attachEvidence,
    unlinkEvidence,
    isAttachingEvidence,
    messages,
    sendMessage,
    suggestedActions,
    steps,
    isStreaming,
    metadata,
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
              <div className="space-y-3">
                <h3 className="text-sm font-bold">{selectedEvidence.title}</h3>
                <p className="text-xs text-muted-foreground">{selectedEvidence.excerpt}</p>
                <div className="space-y-2 border-t pt-3">
                  <label className="text-[11px] font-medium text-muted-foreground">Attach to driver or lever</label>
                  <select
                    className="w-full h-8 px-2 text-[12px] rounded-md border border-border bg-background text-foreground"
                    value={selectedDriverId}
                    onChange={(event) => setSelectedDriverId(event.target.value)}
                  >
                    <option value="">Select driver...</option>
                    {driverOptions.map((driver) => (
                      <option key={driver.id} value={driver.id}>
                        {driver.name ?? driver.hypothesis_text ?? driver.id}
                      </option>
                    ))}
                  </select>
                  <Btn
                    variant="primary"
                    className="w-full"
                    disabled={!selectedDriverId || isAttachingEvidence}
                    onClick={attachEvidence}
                  >
                    {isAttachingEvidence ? "Attaching..." : "Attach Evidence"}
                  </Btn>
                  {evidenceLinks.filter((link) => link.evidence_id === selectedEvidence.id).map((link) => (
                    <button
                      key={`${link.evidence_id}-${link.driver_id}`}
                      className="block w-full text-left text-[10px] text-muted-foreground hover:text-destructive"
                      onClick={() => unlinkEvidence(link)}
                    >
                      Linked to {link.driver_id} - click to unlink
                    </button>
                  ))}
                </div>
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
      <EvidenceTabContent state={{
        account,
        accountLoading,
        evidence,
        isLoading,
        error,
        verified,
        avgMatch,
        selectedEvidence,
        setSelectedEvidence,
        selectedDriverId,
        setSelectedDriverId,
        driverOptions,
        evidenceLinks,
        attachEvidence,
        unlinkEvidence,
        isAttachingEvidence,
        railMode,
        setRailMode,
        messages,
        sendMessage,
        suggestedActions,
        steps,
        isStreaming,
        metadata,
      }} />
    </IntelligenceShell>
  );
}
