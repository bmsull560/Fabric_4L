import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';

const CASE_STORAGE_PREFIX = 'vf.workspace.case';

interface CaseRecord {
  case_id?: string;
  id?: string;
}

function getStoredCaseId(accountId: string): string | null {
  return window.localStorage.getItem(`${CASE_STORAGE_PREFIX}.${accountId}`);
}

function setStoredCaseId(accountId: string, caseId: string) {
  window.localStorage.setItem(`${CASE_STORAGE_PREFIX}.${accountId}`, caseId);
}

export function useCanonicalCaseId(accountId: string | null) {
  return useQuery<string | null>({
    queryKey: ['workspace', 'case-id', accountId],
    enabled: Boolean(accountId),
    queryFn: async () => {
      if (!accountId) return null;

      const stored = getStoredCaseId(accountId);
      if (stored) return stored;

      const lookup = await apiClient.get('l4', `/analysis/cases?account_id=${encodeURIComponent(accountId)}`);
      const items = Array.isArray(lookup.data) ? lookup.data : (lookup.data?.items ?? []);
      const existing = (items[0] ?? {}) as CaseRecord;
      const existingCaseId = existing.case_id || existing.id;
      if (existingCaseId) {
        setStoredCaseId(accountId, existingCaseId);
        return existingCaseId;
      }

      const created = await apiClient.post('l4', '/analysis/cases', {
        account_id: accountId,
        title: `Account ${accountId} workspace`,
      });
      const createdCaseId = String(created.data?.case_id ?? created.data?.id ?? '');
      if (!createdCaseId) throw new Error('Unable to create case for account workspace');
      setStoredCaseId(accountId, createdCaseId);
      return createdCaseId;
    },
  });
}

export function useWorkspaceTabQuery<TData>(caseId: string | null, tabKey: string) {
  return useQuery<TData>({
    queryKey: ['workspace', 'tab', caseId, tabKey],
    enabled: Boolean(caseId),
    queryFn: async () => {
      if (!caseId) throw new Error('Missing case_id');
      try {
        const response = await apiClient.get('l4', `/analysis/cases/${caseId}/workspace/${tabKey}`);
        return response.data as TData;
      } catch (error: unknown) {
        // 501 = workspace tab persistence not yet implemented (H-01).
        // Return empty tab data so the UI renders empty states rather than errors.
        const apiError = error as { statusCode?: number };
        if (apiError.statusCode === 501) {
          return { [tabKey]: [] } as TData;
        }
        throw error;
      }
    },
  });
}

export function usePersistWorkspaceTab(tabKey: string) {
  return useMutation({
    mutationFn: async ({ caseId, payload }: { caseId: string; payload: unknown }) => {
      try {
        const response = await apiClient.put('l4', `/analysis/cases/${caseId}/workspace/${tabKey}`, payload);
        return response.data;
      } catch (error: unknown) {
        // 501 = workspace tab persistence not yet implemented (H-01).
        // Surface as a soft warning so the UI does not crash.
        const apiError = error as { statusCode?: number };
        if (apiError.statusCode === 501) {
          return { case_id: caseId, tab: tabKey, updated: false, not_implemented: true };
        }
        throw error;
      }
    },
  });
}

export function useValidateEvidenceClaim() {
  return useMutation({
    mutationFn: async ({ caseId, evidenceId, claim }: { caseId: string; evidenceId: string; claim: string }) => {
      const response = await apiClient.post('l5', '/claims/validate', {
        case_id: caseId,
        evidence_id: evidenceId,
        claim,
      });
      return response.data;
    },
  });
}

/**
 * Generate workspace intelligence data (signals, drivers, evidence, stakeholders)
 * for a case. Should be called when workspace is first loaded with empty data.
 */
export function useGenerateWorkspaceIntelligence() {
  return useMutation({
    mutationFn: async (caseId: string) => {
      const response = await apiClient.post('l4', `/analysis/cases/${caseId}/workspace/generate`, {});
      return response.data as {
        case_id: string;
        account_id: string;
        generated: boolean;
        stats: {
          signals: number;
          drivers: number;
          evidence: number;
          stakeholders: number;
        };
      };
    },
  });
}

export function useReviewSignalMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      signalId,
      accountId,
      reviewStatus,
      decisionNote,
    }: {
      signalId: string;
      accountId: string;
      reviewStatus: 'approved' | 'rejected';
      decisionNote?: string;
    }) => {
      const response = await apiClient.patch('l4', `/v1/signals/${signalId}/review`, {
        account_id: accountId,
        review_status: reviewStatus,
        decision_note: decisionNote,
      });
      return response.data;
    },
    onSuccess: async (_result, vars) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['workspace', 'tab'] }),
        queryClient.invalidateQueries({ queryKey: QK.accounts.detail(vars.accountId) }),
        queryClient.invalidateQueries({ queryKey: QK.hypotheses.all }),
        queryClient.invalidateQueries({ queryKey: QK.evidence.all }),
      ]);
    },
  });
}
