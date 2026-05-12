import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost, apiPatch } from '@/api/typedClient';
import { QK } from './queryKeys';
import { STALE_TIME, withApiError, BaseApiError } from './useApiShared';

export class GateApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'GateApiError';
  }
}

export interface GateSummary {
  account_id: string;
  all_passed: boolean;
  gates: Array<{
    type: string;
    status: 'open' | 'closed' | 'waived';
    reason: string | null;
  }>;
  checked_at: string;
}

export interface ReviewRequest {
  id: string;
  account_id: string;
  tenant_id: string;
  requester_id: string;
  reviewer_id: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'changes_requested';
  scope: string;
  target_id: string | null;
  comments: Array<{
    id: string;
    review_id: string;
    author_id: string;
    text: string;
    created_at: string;
  }>;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface ReviewCommentPayload {
  id: string;
  text: string;
  author_id: string;
}

export function useAccountGates(accountId: string | null) {
  return useQuery<GateSummary, GateApiError>({
    queryKey: QK.gates.account(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new Error('No account ID provided');
      const response = await apiGet<GateSummary>('l4', `/accounts/${accountId}/gates`);
      return response.data;
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.detail,
  });
}

export function useReviewRequests(accountId: string | null) {
  return useQuery<ReviewRequest[], GateApiError>({
    queryKey: QK.reviews.list(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new Error('No account ID provided');
      const response = await apiGet<ReviewRequest[]>('l4', `/accounts/${accountId}/reviews`);
      return response.data;
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.list,
  });
}

export function useCreateReviewRequest() {
  const qc = useQueryClient();
  return useMutation<ReviewRequest, GateApiError, { accountId: string; reviewerId?: string; scope?: string; targetId?: string }>({
    mutationFn: async ({ accountId, reviewerId, scope = 'business_case', targetId }) => {
      const payload = {
        id: crypto.randomUUID(),
        requester_id: 'current-user',
        reviewer_id: reviewerId || null,
        scope,
        target_id: targetId || null,
      };
      const response = await apiPost<ReviewRequest>('l4', `/accounts/${accountId}/reviews`, payload);
      return response.data;
    },
    onSuccess: (_, { accountId }) => {
      qc.invalidateQueries({ queryKey: QK.reviews.list(accountId) });
      qc.invalidateQueries({ queryKey: QK.gates.account(accountId) });
    },
  });
}

export function useUpdateReviewRequest() {
  const qc = useQueryClient();
  return useMutation<ReviewRequest, GateApiError, { accountId: string; reviewId: string; status: string }>({
    mutationFn: async ({ accountId, reviewId, status }) => {
      const response = await apiPatch<ReviewRequest>('l4', `/accounts/${accountId}/reviews/${reviewId}`, { status });
      return response.data;
    },
    onSuccess: (_, { accountId }) => {
      qc.invalidateQueries({ queryKey: QK.reviews.list(accountId) });
      qc.invalidateQueries({ queryKey: QK.gates.account(accountId) });
    },
  });
}

export function useAddReviewComment() {
  const qc = useQueryClient();
  return useMutation<ReviewRequest, GateApiError, { accountId: string; reviewId: string; comment: ReviewCommentPayload }>({
    mutationFn: async ({ accountId, reviewId, comment }) => {
      await apiPost('l4', `/accounts/${accountId}/reviews/${reviewId}/comments`, comment);
      // Re-fetch the review to get updated comments
      const response = await apiGet<ReviewRequest>('l4', `/accounts/${accountId}/reviews/${reviewId}`);
      return response.data;
    },
    onSuccess: (_, { accountId }) => {
      qc.invalidateQueries({ queryKey: QK.reviews.list(accountId) });
    },
  });
}
