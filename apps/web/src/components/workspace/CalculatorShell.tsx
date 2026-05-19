import { useLocation, useParams } from "react-router-dom";
import WorkspacePagePattern, { type WorkspaceAccountContext } from "@/components/workspace/WorkspacePagePattern";
import { buildPath } from "@/navigation/navigationService";

interface CalculatorShellProps { account: WorkspaceAccountContext; children: React.ReactNode; rightRail?: React.ReactNode; }

const TABS = [
  { key: "roi", label: "ROI" },
  { key: "value-model", label: "Value Model" },
] as const;

export default function CalculatorShell({ account, children, rightRail }: CalculatorShellProps) {
  const { accountId = "" } = useParams<{ accountId: string }>();
  const activeTab = useLocation().pathname.split("/")[3] || "roi";
  return <WorkspacePagePattern account={account} activeTab={activeTab} tabs={TABS.map((t) => ({ ...t, to: buildPath("/calculator/:accountId/:tab", { accountId, tab: t.key }) }))} rightRail={rightRail}>{children}</WorkspacePagePattern>;
}
