/**
 * useWorkspaceContext — Provides account + workspace context to tabs
 */
import { useParams } from "wouter";
import { useAccountContextStore } from "@/stores/accountContextStore";
import { useAccount } from "@/hooks";

export function useWorkspaceContext() {
  const params = useParams<{ accountId: string; tabId: string }>();
  const accountId = params.accountId ?? "";
  const tabId = params.tabId ?? "signals";
  const selectedAccountId = useAccountContextStore((s) => s.selectedAccountId);
  const resolvedAccountId = accountId || selectedAccountId || "";

  const { data: account } = useAccount(resolvedAccountId || null);

  return {
    accountId: resolvedAccountId,
    tabId,
    accountName: account?.name ?? "",
    industry: account?.industry ?? "",
    revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "",
  };
}
