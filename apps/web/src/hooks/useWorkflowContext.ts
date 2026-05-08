import { useMemo } from "react";
import { useLocation } from "react-router-dom";
import { useWorkflowStore } from "@/workflow/store/workflowStore";
import { WORKFLOW_CONTEXT_QUERY_KEYS, type WorkflowContext } from "@/workflow/context";

export function useWorkflowContext(): Partial<WorkflowContext> {
  const location = useLocation();
  const workflowContext = useWorkflowStore((s) => s.workflowContext);

  return useMemo(() => {
    const query = new URLSearchParams(location.search);
    const accountId = query.get(WORKFLOW_CONTEXT_QUERY_KEYS.accountId) ?? workflowContext.accountId;
    const sessionId = query.get(WORKFLOW_CONTEXT_QUERY_KEYS.sessionId) ?? workflowContext.sessionId;
    const activeTab = query.get(WORKFLOW_CONTEXT_QUERY_KEYS.activeTab) ?? workflowContext.step?.activeTab;
    const stepIndex = query.get(WORKFLOW_CONTEXT_QUERY_KEYS.activeStep);

    return {
      ...workflowContext,
      accountId: accountId ?? undefined,
      sessionId: sessionId ?? undefined,
      step: {
        stepIndex: stepIndex !== null ? Number(stepIndex) : workflowContext.step?.stepIndex ?? 0,
        stepKey: workflowContext.step?.stepKey ?? "unknown",
        activeTab: activeTab ?? undefined,
      },
      workspaceCaseId: query.get(WORKFLOW_CONTEXT_QUERY_KEYS.workspaceCaseId) ?? workflowContext.workspaceCaseId,
      driverTreeId: query.get(WORKFLOW_CONTEXT_QUERY_KEYS.driverTreeId) ?? workflowContext.driverTreeId,
      scenarioId: query.get(WORKFLOW_CONTEXT_QUERY_KEYS.scenarioId) ?? workflowContext.scenarioId,
      businessCaseId: query.get(WORKFLOW_CONTEXT_QUERY_KEYS.businessCaseId) ?? workflowContext.businessCaseId,
    };
  }, [location.search, workflowContext]);
}
