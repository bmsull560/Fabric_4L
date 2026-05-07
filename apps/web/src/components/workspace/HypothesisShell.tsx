import { useLocation, useParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { useNavigation } from "@/hooks/useNavigation";
import { Btn } from "@/components/WfPrimitives";
import WorkspacePagePattern, { type WorkspaceAccountContext } from "@/components/workspace/WorkspacePagePattern";

interface HypothesisShellProps { account: WorkspaceAccountContext; children: React.ReactNode; rightRail?: React.ReactNode; }
const TABS = [
  { key: "hypothesis", label: "Hypotheses" },
  { key: "discovery-questions", label: "Discovery Questions" },
  { key: "persona-fit", label: "Persona Fit" },
  { key: "assumptions", label: "Assumptions" },
] as const;

export default function HypothesisShell({ account, children, rightRail }: HypothesisShellProps) {
  const { accountId = "" } = useParams<{ accountId: string }>();
  const activeTab = useLocation().pathname.split("/")[3] || "hypothesis";
  const { navigateTo } = useNavigation();
  return <WorkspacePagePattern account={account} activeTab={activeTab} tabs={TABS.map((t)=>({ ...t, to:`/hypothesis/${accountId}/${t.key}` }))} rightRail={rightRail} headerAction={<Btn variant="primary" onClick={() => navigateTo("drivers", { accountId })} className="gap-1.5"><Sparkles size={13} />Generate Driver Tree</Btn>}>{children}</WorkspacePagePattern>;
}
