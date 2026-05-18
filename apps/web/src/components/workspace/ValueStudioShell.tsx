import { Link, useLocation, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Btn } from "@/components/WfPrimitives";
import WorkspacePagePattern, { type WorkspaceAccountContext } from "@/components/workspace/WorkspacePagePattern";
import { buildPath } from "@/navigation/navigationService";
interface ValueStudioShellProps { account: WorkspaceAccountContext; children: React.ReactNode; rightRail?: React.ReactNode; }
const TABS = [
  { key: "action-plan", label: "Action Plan" },
  { key: "value-model", label: "Value Model" },
  { key: "narrative", label: "Narrative" },
  { key: "enrichment", label: "Enrichment" },
  { key: "competitive", label: "Competitive" },
  { key: "roi", label: "ROI" },
  { key: "evidence", label: "Evidence" },
] as const;
export default function ValueStudioShell({ account, children, rightRail }: ValueStudioShellProps) {
  const { accountId = "" } = useParams<{ accountId: string }>();
  const activeTab = useLocation().pathname.split("/")[3] || "action-plan";
  return <WorkspacePagePattern account={account} activeTab={activeTab} tabs={TABS.map((t) => ({ ...t, to: buildPath("/studio/:accountId/:tab", { accountId, tab: t.key }) }))} rightRail={rightRail} headerAction={<Link to={buildPath("/intelligence/:accountId/:tab", { accountId, tab: "signals" })}><Btn variant="outline" className="gap-1.5"><ArrowLeft size={13} />Back to Intelligence</Btn></Link>}>{children}</WorkspacePagePattern>;
}
