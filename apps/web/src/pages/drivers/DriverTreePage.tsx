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
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { EvidenceTabContent } from "@/pages/intelligence/EvidenceTab";
import AlternativesTab from "@/pages/evidence/AlternativesTab";
import SolutionCostTab from "@/pages/evidence/SolutionCostTab";

export default function DriverTreePage() {
  const params = useParams<{ accountId: string; tab?: string }>();
  const { accountId, tab = "evidence" } = params;
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <LoadingState message="Loading driver tree…" fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;
  }

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
