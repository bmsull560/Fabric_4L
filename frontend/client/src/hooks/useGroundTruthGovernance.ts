import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { components } from "@/api/generated/l5-types";
import { QK } from "./queryKeys";
import {
  withApiError,
  BaseApiError,
  STALE_TIME,
  RETRY_CONFIG,
} from "./useApiShared";

export type TruthStatus = components["schemas"]["TruthStatus"];
export type TruthObjectSummary = components["schemas"]["TruthObjectSummary"];
export type ValidationEventResponse =
  components["schemas"]["ValidationEventResponse"];
export type MaturityLadderResponse =
  components["schemas"]["MaturityLadderResponse"];

export interface TruthListFilters {
  status?: TruthStatus;
  claim_type?: components["schemas"]["ClaimType"];
  min_maturity?: number;
  min_confidence?: number;
  is_stale?: boolean;
  applies_to_opportunity?: string;
  limit?: number;
  offset?: number;
}

export interface FreshnessSummaryResponse {
  stale_count?: number;
  fresh_count?: number;
  expiring_soon_count?: number;
  total_count?: number;
  [key: string]: unknown;
}

export interface StaleTruthsResponse {
  items: TruthObjectSummary[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  [key: string]: unknown;
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
): Promise<components["schemas"]["TruthObjectListResponse"]> {
  const response = (await apiClient.get(
    "l5",
    `/truths${toQueryString(filters)}`
  )) as { data: unknown };
  return response.data as components["schemas"]["TruthObjectListResponse"];
}

async function fetchTruthAuditTrail(
  truthId: string
): Promise<ValidationEventResponse[]> {
  const response = (await apiClient.get(
    "l5",
    `/truths/${encodeURIComponent(truthId)}/audit`
  )) as { data: unknown };
  return response.data as ValidationEventResponse[];
}

async function fetchFreshnessSummary(): Promise<FreshnessSummaryResponse> {
  const response = (await apiClient.get(
    "l5",
    "/truths/freshness-summary"
  )) as { data: unknown };
  return response.data as FreshnessSummaryResponse;
}

function normalizeTruthItems(data: unknown): TruthObjectSummary[] {
  if (Array.isArray(data)) {
    return data as TruthObjectSummary[];
  }
  if (
    data &&
    typeof data === "object" &&
    Array.isArray((data as { items?: unknown }).items)
  ) {
    return (data as { items: TruthObjectSummary[] }).items;
  }
  return [];
}

async function fetchStaleTruths(
  params: Pick<TruthListFilters, "limit" | "offset">
): Promise<StaleTruthsResponse> {
  const response = (await apiClient.get(
    "l5",
    `/truths/stale${toQueryString(params)}`
  )) as { data: unknown };
  const payload = response.data as Record<string, unknown>;
  const items = normalizeTruthItems(payload);

  return {
    ...payload,
    items,
    total: typeof payload.total === "number" ? payload.total : items.length,
    limit:
      typeof payload.limit === "number"
        ? payload.limit
        : (params.limit ?? items.length),
    offset:
      typeof payload.offset === "number"
        ? payload.offset
        : (params.offset ?? 0),
    has_more: Boolean(payload.has_more),
  };
}

async function fetchMaturityLadder(): Promise<MaturityLadderResponse> {
  const response = (await apiClient.get("l5", "/maturity-ladder")) as {
    data: unknown;
  };
  return response.data as MaturityLadderResponse;
}

export function useTruths(filters: TruthListFilters = {}) {
  return useQuery<
    components["schemas"]["TruthObjectListResponse"],
    GroundTruthGovernanceApiError
  >({
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
