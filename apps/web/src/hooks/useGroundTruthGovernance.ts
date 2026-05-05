import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type {
  ClaimType,
  FreshnessSummaryResponse,
  MaturityLadderResponse,
  StaleTruthsResponse,
  TruthObjectListResponse,
  TruthStatus,
  ValidationEventResponse,
} from "@/lib/schemas/groundTruthGovernance";
import {
  parseFreshnessSummaryResponse,
  parseMaturityLadderResponse,
  parseStaleTruthsResponse,
  parseTruthObjectListResponse,
  parseValidationEventListResponse,
} from "@/lib/schemas/groundTruthGovernance";
import { QK } from "./queryKeys";
import {
  withApiError,
  BaseApiError,
  STALE_TIME,
  RETRY_CONFIG,
} from "./useApiShared";

export type {
  ClaimType,
  FreshnessSummaryResponse,
  MaturityLadderResponse,
  StaleTruthsResponse,
  TruthObjectListResponse,
  TruthObjectSummary,
  TruthStatus,
  ValidationEventResponse,
} from "@/lib/schemas/groundTruthGovernance";

export interface TruthListFilters {
  status?: TruthStatus;
  claim_type?: ClaimType;
  min_maturity?: number;
  min_confidence?: number;
  is_stale?: boolean;
  applies_to_opportunity?: string;
  limit?: number;
  offset?: number;
}

export class GroundTruthGovernanceApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = "GroundTruthGovernanceApiError";
  }
}

function toQueryString(filters: object): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

async function fetchTruths(
  filters: TruthListFilters
): Promise<TruthObjectListResponse> {
  const response = (await apiClient.get(
    "l4",
    `/ground-truth/truths${toQueryString(filters)}`
  )) as { data: unknown };
  return parseTruthObjectListResponse(response.data);
}

async function fetchTruthAuditTrail(
  truthId: string
): Promise<ValidationEventResponse[]> {
  const response = (await apiClient.get(
    "l4",
    `/ground-truth/truths/${encodeURIComponent(truthId)}/audit`
  )) as { data: unknown };
  return parseValidationEventListResponse(response.data);
}

async function fetchFreshnessSummary(): Promise<FreshnessSummaryResponse> {
  const response = (await apiClient.get(
    "l4",
    "/ground-truth/truths/freshness-summary"
  )) as { data: unknown };
  return parseFreshnessSummaryResponse(response.data);
}

async function fetchStaleTruths(
  params: Pick<TruthListFilters, "limit" | "offset">
): Promise<StaleTruthsResponse> {
  const response = (await apiClient.get(
    "l4",
    `/ground-truth/truths/stale${toQueryString(params)}`
  )) as { data: unknown };
  return parseStaleTruthsResponse(response.data, params);
}

async function fetchMaturityLadder(): Promise<MaturityLadderResponse> {
  const response = (await apiClient.get("l4", "/ground-truth/maturity-ladder")) as {
    data: unknown;
  };
  return parseMaturityLadderResponse(response.data);
}

export function useTruths(filters: TruthListFilters = {}) {
  return useQuery<TruthObjectListResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.list(filters),
    queryFn: () =>
      withApiError(fetchTruths(filters), GroundTruthGovernanceApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useTruthAuditTrail(truthId: string | null) {
  return useQuery<ValidationEventResponse[], GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.audit(truthId ?? ""),
    enabled: Boolean(truthId),
    queryFn: async () => {
      if (!truthId)
        throw new GroundTruthGovernanceApiError("No truth ID provided");
      return withApiError(
        fetchTruthAuditTrail(truthId),
        GroundTruthGovernanceApiError
      );
    },
    staleTime: STALE_TIME.activity,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useTruthFreshnessSummary() {
  return useQuery<FreshnessSummaryResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.freshnessSummary(),
    queryFn: () =>
      withApiError(fetchFreshnessSummary(), GroundTruthGovernanceApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useStaleTruths(
  params: Pick<TruthListFilters, "limit" | "offset"> = {}
) {
  return useQuery<StaleTruthsResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.stale(params),
    queryFn: () =>
      withApiError(fetchStaleTruths(params), GroundTruthGovernanceApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useMaturityLadder() {
  return useQuery<MaturityLadderResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.maturityLadder(),
    queryFn: () =>
      withApiError(fetchMaturityLadder(), GroundTruthGovernanceApiError),
    staleTime: STALE_TIME.reference,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
