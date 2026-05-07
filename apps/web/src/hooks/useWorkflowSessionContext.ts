import { useEffect, useMemo } from "react";
import { useLocation, useParams } from "react-router-dom";
import { useWorkflowSessionStore } from "@/stores/workflowSessionStore";

const OPEN_TABS = new Set(["signals", "hypothesis", "trees", "roi", "narrative"]);

export function useWorkflowSessionContext() {
  const params = useParams<{ accountId?: string; tab?: string; tabId?: string }>();
  const location = useLocation();
  const { context, setContext, clearContext } = useWorkflowSessionStore();

  const urlContext = useMemo(() => {
    const search = new URLSearchParams(location.search);
    const tabParam = params.tabId ?? params.tab ?? search.get("tab");
    const tabId = tabParam && OPEN_TABS.has(tabParam) ? tabParam : null;

    return {
      accountId: params.accountId ?? search.get("accountId"),
      caseId: search.get("caseId"),
      selectedEntityId: search.get("entityId"),
      tabId,
      lastPath: `${location.pathname}${location.search}`,
    };
  }, [location.pathname, location.search, params.accountId, params.tab, params.tabId]);

  useEffect(() => {
    const hydrated = {
      accountId: urlContext.accountId ?? context.accountId,
      caseId: urlContext.caseId ?? context.caseId,
      selectedEntityId: urlContext.selectedEntityId ?? context.selectedEntityId,
      tabId: urlContext.tabId ?? context.tabId,
      lastPath: urlContext.lastPath,
    };

    setContext(hydrated);
  }, [context.accountId, context.caseId, context.selectedEntityId, context.tabId, setContext, urlContext]);

  const staleReason = useMemo(() => {
    if (!context.accountId && location.pathname.startsWith("/intelligence")) return "missing-account";
    if (context.caseId === "closed") return "case-closed";
    if (context.selectedEntityId === "deleted") return "entity-deleted";
    return null;
  }, [context, location.pathname]);

  return {
    workflowContext: context,
    staleReason,
    clearWorkflowContext: clearContext,
  };
}
