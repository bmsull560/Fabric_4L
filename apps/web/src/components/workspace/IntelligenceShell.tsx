import { useLocation, useParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { useNavigation } from "@/hooks/useNavigation";
import WorkspacePagePattern, { type WorkspaceAccountContext } from "@/components/workspace/WorkspacePagePattern";
import { buildPath } from "@/navigation/navigationService";
import { Btn } from "@/components/ui/fabric";
interface IntelligenceShellProps { account: WorkspaceAccountContext; children: React.ReactNode; rightRail?: React.ReactNode; }
const TABS = [
  { key: "signals", label: "Signals" },
  { key: "stakeholders", label: "Stakeholder Map" },
  { key: "ontology-match", label: "Ontology Match" },
  { key: "enrichment", label: "Enrichment" },
] as const;
export default function IntelligenceShell({ account, children, rightRail }: IntelligenceShellProps) {
  const { accountId = "" } = useParams<{ accountId: string }>();
  const activeTab = useLocation().pathname.split("/")[3] || "signals";
  const { navigateTo } = useNavigation();
  return <WorkspacePagePattern account={account} activeTab={activeTab} tabs={TABS.map((t) => ({ ...t, to: buildPath("/intelligence/:accountId/:tab", { accountId, tab: t.key }) }))} rightRail={rightRail} headerAction={<Btn variant="primary" onClick={() => navigateTo("hypothesis", { accountId })} className="gap-1.5"><Sparkles size={13} />Generate AI Value Model</Btn>}>{children}</WorkspacePagePattern>;
}
