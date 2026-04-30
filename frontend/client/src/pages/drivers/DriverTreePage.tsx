/**
 * DriverTreePage — Driver Tree workspace entry point
 *
 * Route: /drivers/:accountId/:tab?
 *
 * Tabs: Evidence | Alternatives | Solution Cost
 */
import { useParams } from "react-router-dom";
import DriverTreeShell from "@/components/workspace/DriverTreeShell";
import { useAccount } from "@/hooks/useAccounts";
import { EvidenceTabContent } from "@/pages/intelligence/EvidenceTab";
import AlternativesTab from "@/pages/evidence/AlternativesTab";
import SolutionCostTab from "@/pages/evidence/SolutionCostTab";

export default function DriverTreePage() {
  const params = useParams<{ accountId: string; tab?: string }>();
  const { accountId, tab = "evidence" } = params;
  const { data: account } = useAccount(accountId ?? null);

  const accountName = account?.name ?? "Account";
  const industry = account?.industry ?? "Unknown";
  const revenue = account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A";

  return (
    <DriverTreeShell accountName={accountName} industry={industry} revenue={revenue}>
      {tab === "evidence" && <EvidenceTabContent />}
      {tab === "alternatives" && <AlternativesTab />}
      {tab === "solution-cost" && <SolutionCostTab />}
    </DriverTreeShell>
  );
}
