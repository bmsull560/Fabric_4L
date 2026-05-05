import { useQuery, useMutation } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { QK } from "./queryKeys";
import { STALE_TIME } from "./useApiShared";
import {
  parseAuditLogResponse,
  parseProvenanceTrail,
  type AuditLogEntry,
  type AuditLogResponse,
  type ProvenanceStep,
  type ProvenanceTrail,
} from "@/lib/schemas/provenance";

export type {
  AuditLogEntry,
  AuditLogResponse,
  ProvenanceStep,
  ProvenanceTrail,
};

export interface AuditLogFilter {
  source?: "provenance" | "access" | "all";
  from_date?: string;
  to_date?: string;
  entity_type?: string;
  event_type?: string;
  agent?: string;
}

export function useProvenanceTrail(entityId: string | null) {
  return useQuery({
    queryKey: QK.provenance.trail(entityId || ""),
    queryFn: async () => {
      if (!entityId) throw new Error("No entity ID provided");
      const response = await apiClient.get(
        "l3",
        `/provenance/${encodeURIComponent(entityId)}`
      );
      return parseProvenanceTrail(response.data);
    },
    enabled: !!entityId,
    staleTime: STALE_TIME.activity,
  });
}

export function useAuditLogs(filters: AuditLogFilter = {}) {
  return useQuery({
    queryKey: QK.provenance.audit(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.source) params.set("source", filters.source);
      if (filters.from_date) params.set("from_date", filters.from_date);
      if (filters.to_date) params.set("to_date", filters.to_date);
      if (filters.entity_type) params.set("entity_type", filters.entity_type);
      if (filters.event_type) params.set("event_type", filters.event_type);
      if (filters.agent) params.set("agent", filters.agent);

      const response = await apiClient.get(
        "l3",
        `/audit/logs?${params.toString()}`
      );
      return parseAuditLogResponse(response.data);
    },
    staleTime: STALE_TIME.poll,
  });
}

export function useExportProvenance() {
  return useMutation({
    mutationFn: async ({
      entityId,
      format = "json",
    }: {
      entityId: string;
      format?: "json" | "prov-o";
    }) => {
      const response = await apiClient.get(
        "l3",
        `/provenance/${encodeURIComponent(entityId)}?format=${format}`
      );
      return response.data;
    },
  });
}
