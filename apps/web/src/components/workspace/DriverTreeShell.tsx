import { useLocation, useParams } from "react-router-dom";
import WorkspacePagePattern, { type WorkspaceAccountContext } from "@/components/workspace/WorkspacePagePattern";
const TABS = [
  { key: "trees", label: "Trees" },
  { key: "evidence", label: "Evidence" },
  { key: "alternatives", label: "Alternatives" },
  { key: "solution-cost", label: "Solution Cost" },
] as const;
interface DriverTreeShellProps extends Partial<WorkspaceAccountContext> { children: React.ReactNode; }
export default function DriverTreeShell({ accountName = "Account", industry = "Unknown", revenue = "N/A", children }: DriverTreeShellProps) {
  const { accountId = "" } = useParams<{ accountId: string }>();
  const activeTab = useLocation().pathname.split("/")[3] || "trees";
  return <WorkspacePagePattern account={{ accountName, industry, revenue }} activeTab={activeTab} tabs={TABS.map((t)=>({ ...t, to:`/drivers/${accountId}/${t.key}` }))}>{children}</WorkspacePagePattern>;
}
