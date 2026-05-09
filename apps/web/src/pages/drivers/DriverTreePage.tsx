/**
 * DriverTreePage — Driver Tree workspace entry point
 *
 * Route: /drivers/:accountId/:tab?
 *
 * Tabs: Trees | Evidence | Alternatives | Solution Cost
 */
import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import DriverTreeShell from "@/components/workspace/DriverTreeShell";
import { useAccount } from "@/hooks/useAccounts";
import { useAccountHypotheses } from "@/hooks/useHypotheses";
import { useValueTreePaths } from "@/hooks/useValueTrees";
import { useCanonicalCaseId, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { useNavigation } from "@/hooks";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState, EmptyState } from "@/components/states";
import { SectionCard, Btn } from "@/components/WfPrimitives";
import { EvidenceTabContent } from "@/pages/intelligence/EvidenceTab";
import AlternativesTab from "@/pages/evidence/AlternativesTab";
import SolutionCostTab from "@/pages/evidence/SolutionCostTab";
import { TreePine, ArrowRight } from "lucide-react";
import { useWorkspaceSelectionStore } from "@/stores/workspaceSelectionStore";
import { useWorkflowSessionContext } from "@/hooks/useWorkflowSessionContext";

interface PromotedDriver {
  id?: string;
  hypothesis_id?: string;
  name?: string;
  hypothesis_text?: string;
  category?: string;
  value_path_category?: string;
  confidence?: number;
  capability_id?: string;
}

export default function DriverTreePage() {
  const params = useParams<{ accountId: string; tab?: string }>();
  const { accountId, tab = "trees" } = params;
  const { navigateTo } = useNavigation();
  const location = useLocation();
  const setSelection = useWorkspaceSelectionStore((state) => state.setSelection);
  const getSelection = useWorkspaceSelectionStore((state) => state.getSelection);
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);
  const { staleReason, clearWorkflowContext } = useWorkflowSessionContext();
  const { data: hypothesesData, isLoading: hypothesesLoading } = useAccountHypotheses(
    accountId ?? null,
    { status: 'validated' }
  );
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const driversQuery = useWorkspaceTabQuery<{ drivers?: PromotedDriver[] }>(caseId ?? null, "drivers");
  const linksQuery = useWorkspaceTabQuery<{ evidence_links?: Array<{ evidence_id: string; driver_id: string }> }>(caseId ?? null, "evidence-links");
  const [selectedTreeId, setSelectedTreeId] = useState<string | null>(null);

  useEffect(() => {
    if (!accountId) return;
    const params = new URLSearchParams(location.search);
    const treeId = params.get("tree_id") || null;
    const valueModelId = params.get("value_model_id") || null;
    if (treeId || valueModelId) {
      setSelection(accountId, { treeId, valueModelId });
      if (treeId) setSelectedTreeId(treeId);
      return;
    }
    const persisted = getSelection(accountId);
    if (persisted.treeId) {
      setSelectedTreeId(persisted.treeId);
    }
  }, [accountId, location.search, getSelection, setSelection]);

  useEffect(() => {
    if (accountId && !accountLoading && !account) {
      clearWorkflowContext();
    }
  }, [accountId, accountLoading, account, clearWorkflowContext]);

  const accountName = account?.name ?? "Account";
  const industry = account?.industry ?? "Unknown";
  const revenue = account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A";

  const hypotheses = hypothesesData?.hypotheses ?? [];
  const promotedDrivers = driversQuery.data?.drivers ?? [];
  const treeItems = promotedDrivers.length > 0
    ? promotedDrivers.map((driver) => ({
        id: String(driver.id ?? driver.hypothesis_id ?? ""),
        title: String(driver.name ?? driver.hypothesis_text ?? "Promoted value driver"),
        valuePath: String(driver.category ?? driver.value_path_category ?? "Unclassified"),
        confidence: Number(driver.confidence ?? 0.5),
        capabilityId: typeof driver.capability_id === "string" ? driver.capability_id : undefined,
      }))
    : hypotheses.map((h) => ({
        id: h.id,
        title: h.hypothesis_text,
        valuePath: h.value_path_category ?? "Unclassified",
        confidence: h.confidence ?? 0.5,
        capabilityId: h.capability_id,
      }));
  const selectedTree = treeItems.find((item) => item.id === selectedTreeId);
  const capabilityId = selectedTree?.capabilityId;
  const evidenceLinks = linksQuery.data?.evidence_links ?? [];

  const { data: treePaths, isLoading: pathsLoading } = useValueTreePaths(
    capabilityId,
    { direction: 'upward', maxDepth: 4, enabled: !!capabilityId }
  );

  const driverTabIsLoading = hypothesesLoading || driversQuery.isLoading || linksQuery.isLoading;
  const driverTabError = driversQuery.error ?? linksQuery.error;

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <LoadingState message="Loading driver tree…" fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found." description="Select a valid account to continue in this workspace." fullPage />;
  }

  if (staleReason === "case-closed" || staleReason === "entity-deleted") {
    return (
      <ErrorState
        title="Saved workflow context is stale"
        description="The saved case or entity is no longer available. Start from the current account workspace."
        fullPage
      />
    );
  }

  const TreesTab = () => (
    <div className="space-y-6">
      {driverTabIsLoading ? (
        <LoadingState message="Loading driver tree suggestions…" />
      ) : driverTabError ? (
        <ErrorState
          title="Unable to load driver tree data"
          description="We could not load drivers or evidence links. Please retry from Intelligence or refresh this page."
        />
      ) : treeItems.length === 0 ? (
        <EmptyState
          title="No driver tree suggestions"
          description="No drivers have been promoted yet. Approve and convert a hypothesis from Intelligence to create your first driver tree."
          icon={TreePine}
          action={
            <Btn onClick={() => navigateTo('intelligence-signals', { accountId })}>
              Go to Signals
            </Btn>
          }
        />
      ) : (
        <>
          <SectionCard title="Suggested Driver Trees">
            <div className="space-y-3">
              {treeItems.map((h) => {
                const linkedEvidenceCount = evidenceLinks.filter((link) => link.driver_id === h.id).length;
                return (
                <div
                  key={h.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedTreeId === h.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                  onClick={() => setSelectedTreeId(h.id)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-foreground">{h.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        Value Path: {h.valuePath} · Confidence: {Math.round(h.confidence * 100)}% · Evidence Links: {linkedEvidenceCount}
                      </p>
                    </div>
                    {selectedTreeId === h.id && (
                      <Btn
                        variant="primary"
                        onClick={() => navigateTo('calculator', { accountId }, { query: { hypothesisId: h.id } })}
                      >
                        Model Impact <ArrowRight size={12} />
                      </Btn>
                    )}
                  </div>
                </div>
              );
              })}
            </div>
          </SectionCard>

          {selectedTreeId && capabilityId && (
            <SectionCard title="Value Tree Paths">
              {pathsLoading ? (
                <LoadingState message="Loading value tree paths…" />
              ) : !treePaths || treePaths.length === 0 ? (
                <EmptyState
                  title="No value tree paths"
                  description="This capability is not yet linked to any value drivers in the knowledge graph."
                  icon={TreePine}
                />
              ) : (
                <div className="space-y-3">
                  {treePaths.map((path, idx) => (
                    <div key={idx} className="border rounded-lg p-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        {path.nodes.map((node, nIdx) => (
                          <span key={node.id} className="flex items-center gap-2">
                            <span className="px-2 py-1 rounded bg-muted text-xs font-medium">
                              {node.name}
                            </span>
                            {nIdx < path.nodes.length - 1 && (
                              <ArrowRight size={12} className="text-muted-foreground" />
                            )}
                          </span>
                        ))}
                      </div>
                      <p className="text-[10px] text-muted-foreground mt-1">
                        {path.length} hops · {path.nodes.length} nodes
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          )}
        </>
      )}
    </div>
  );

  return (
    <DriverTreeShell accountName={accountName} industry={industry} revenue={revenue}>
      {tab === "trees" && <TreesTab />}
      {tab === "evidence" && <EvidenceTabContent />}
      {import.meta.env.VITE_ENABLE_DRIVER_TREE_EXPERIMENTAL_TABS === "true" && tab === "alternatives" && <AlternativesTab />}
      {import.meta.env.VITE_ENABLE_DRIVER_TREE_EXPERIMENTAL_TABS === "true" && tab === "solution-cost" && <SolutionCostTab />}
    </DriverTreeShell>
  );
}
