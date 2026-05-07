import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/api/typedClient";
import { QK } from "./queryKeys";
import {
  withApiError,
  BaseApiError,
  STALE_TIME,
  RETRY_CONFIG,
} from "./useApiShared";

export interface OperationalAuditEntry {
  id: string;
  timestamp: string;
  source: "access_log";
  event_type: string;
  entity_id: string | null;
  entity_type: string | null;
  action: string;
  agent: string;
  details: Record<string, unknown>;
}

export interface OperationalAuditResponse {
  entries: OperationalAuditEntry[];
  total: number;
  page: number;
  per_page: number;
}

export interface OperationalAuditFilters {
  eventType?: string;
  entityType?: string;
  page?: number;
  perPage?: number;
}

export class OperationalAuditApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = "OperationalAuditApiError";
  }
}

async function fetchOperationalAudit(
  filters: OperationalAuditFilters
): Promise<OperationalAuditResponse> {
  const params = new URLSearchParams();
  params.set("source", "access");
  params.set("page", String(filters.page ?? 1));
  params.set("per_page", String(filters.perPage ?? 25));

  if (filters.eventType) {
    params.set("event_type", filters.eventType);
  }
  if (filters.entityType) {
    params.set("entity_type", filters.entityType);
  }

  const response = await apiGet<OperationalAuditResponse>(
    "l4",
    `/audit/logs?${params.toString()}`
  );
  return response.data;
}

export function useOperationalAudit(filters: OperationalAuditFilters = {}) {
  return useQuery<OperationalAuditResponse, OperationalAuditApiError>({
    queryKey: [...QK.governance.all, "operational-audit", filters] as const,
    queryFn: () =>
      withApiError(fetchOperationalAudit(filters), OperationalAuditApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
