/**
 * useBusinessCasePage — Tier-3 Page Orchestration Hook
 *
 * Orchestrates business case data fetching, export mutations, and navigation actions.
 * Provides a stable boundary between atomic data hooks and UI state.
 *
 * @example
 * ```ts
 * const {
 *   businessCase,
 *   actions,
 *   status,
 * } = useBusinessCasePage(businessCaseId);
 * ```
 */

import { useCallback } from "react";
import { useBusinessCase, useBusinessCaseExport } from "@/hooks/useDocuments";
import { useNavigation } from "@/hooks";

// Page hook return type
export interface UseBusinessCasePageReturn {
  // Data
  businessCase: ReturnType<typeof useBusinessCase>["data"];
  
  // Actions
  actions: {
    handleExportPDF: () => void;
    handleViewTrace: () => void;
    handleExploreInteractive: () => void;
  };
  
  // Status
  status: {
    isLoading: boolean;
    error: Error | null;
    isExporting: boolean;
  };
}

export function useBusinessCasePage(businessCaseId: string | null): UseBusinessCasePageReturn {
  const { navigateTo } = useNavigation();

  // Atomic data hooks
  const { data: businessCase, isLoading, error } = useBusinessCase(businessCaseId);
  const exportMutation = useBusinessCaseExport();

  // Actions
  const handleExportPDF = useCallback(() => {
    if (!businessCase || !businessCaseId) return;
    exportMutation.mutate({
      caseId: businessCaseId,
      format: "pdf",
    });
  }, [businessCase, businessCaseId, exportMutation]);

  const handleViewTrace = useCallback(() => {
    if (businessCaseId) {
      navigateTo('decision-trace', undefined, { query: { caseId: businessCaseId } });
    }
  }, [businessCaseId, navigateTo]);

  const handleExploreInteractive = useCallback(() => {
    if (businessCaseId) {
      navigateTo('business-case-interactive', undefined, { query: { id: businessCaseId } });
    }
  }, [businessCaseId, navigateTo]);

  return {
    businessCase,
    actions: {
      handleExportPDF,
      handleViewTrace,
      handleExploreInteractive,
    },
    status: {
      isLoading,
      error: error ?? null,
      isExporting: exportMutation.isPending,
    },
  };
}
