/**
 * useWorkspaceContext — Provides account + workspace context to tabs
 */
import { useParams } from "wouter";
import { useAccountContextStore } from "@/stores/accountContextStore";

export function useWorkspaceContext() {
  const params = useParams<{ accountId: string; tabId: string }>();
  const accountId = params.accountId ?? "";
  const tabId = params.tabId ?? "signals";
  const selectedAccountId = useAccountContextStore((s) => s.selectedAccountId);

  return {
    accountId: accountId || selectedAccountId || "",
    tabId,
    accountName: "",
    industry: "",
    revenue: "",
  };
}
