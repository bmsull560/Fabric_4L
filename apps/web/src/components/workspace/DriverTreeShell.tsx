import { useLocation, useParams } from "react-router-dom";
import WorkspacePagePattern, { type WorkspaceAccountContext } from "@/components/workspace/WorkspacePagePattern";
import { buildPath } from "@/navigation/navigationService";
const ENABLE_EXPERIMENTAL_DRIVER_TABS = import.meta.env.VITE_ENABLE_DRIVER_TREE_EXPERIMENTAL_TABS === "true";

const TABS = [
  { key: "trees", label: "Trees" },
  { key: "evidence", label: "Evidence" },
  ...(ENABLE_EXPERIMENTAL_DRIVER_TABS
    ? [
        { key: "alternatives", label: "Alternatives" },
        { key: "solution-cost", label: "Solution Cost" },
      ]
    : []),
] as const;
interface DriverTreeShellProps extends Partial<WorkspaceAccountContext> { children: React.ReactNode; }
export default function DriverTreeShell({ accountName = "Account", industry = "Unknown", revenue = "N/A", children }: DriverTreeShellProps) {
  const { accountId = "" } = useParams<{ accountId: string }>();
  const activeTab = useLocation().pathname.split("/")[3] || "trees";
  return <WorkspacePagePattern account={{ accountName, industry, revenue }} activeTab={activeTab} tabs={TABS.map((t) => ({ ...t, to: buildPath("/drivers/:accountId/:tab", { accountId, tab: t.key }) }))}>{children}</WorkspacePagePattern>;
}
