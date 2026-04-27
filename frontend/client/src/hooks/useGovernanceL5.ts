import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export interface TruthRecord {
  id: string;
  claim: string;
  status: string;
  maturity_level?: string;
  updated_at?: string;
}

export interface TruthsResponse {
  items: TruthRecord[];
  total: number;
}

export interface MaturityLadderLevel {
  level: string;
  description: string;
  threshold?: number;
}

export interface AuditEvent {
  id: string;
  action: string;
  entity_id?: string;
  changed_fields?: string[];
  timestamp: string;
}

export interface GovernanceTruthQuery {
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

function buildQuery(params: GovernanceTruthQuery = {}): string {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.search) query.set('search', params.search);
  if (params.limit != null) query.set('limit', String(params.limit));
  if (params.offset != null) query.set('offset', String(params.offset));
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await axios.get<T>(path);
  return response.data;
}

export function useGovernanceTruths(params: GovernanceTruthQuery = {}) {
  return useQuery<TruthsResponse, Error>({
    queryKey: ['governance-l5', 'truths', params],
    queryFn: () => fetchJson<TruthsResponse>(`/api/v1/truths${buildQuery(params)}`),
  });
}

export function useGovernanceMaturityLadder() {
  return useQuery<MaturityLadderLevel[], Error>({
    queryKey: ['governance-l5', 'maturity-ladder'],
    queryFn: () => fetchJson<MaturityLadderLevel[]>('/api/v1/maturity-ladder'),
  });
}

export function useGovernanceFreshnessSummary() {
  return useQuery<Record<string, number>, Error>({
    queryKey: ['governance-l5', 'freshness-summary'],
    queryFn: () => fetchJson<Record<string, number>>('/api/v1/truths/freshness-summary'),
  });
}

export function useGovernanceAuditLog() {
  return useQuery<AuditEvent[], Error>({
    queryKey: ['governance-l5', 'audit', 'log'],
    queryFn: () => fetchJson<AuditEvent[]>('/api/v1/truths/audit/log'),
  });
}

export function useGovernanceAuditChanges() {
  return useQuery<AuditEvent[], Error>({
    queryKey: ['governance-l5', 'audit', 'changes'],
    queryFn: () => fetchJson<AuditEvent[]>('/api/v1/truths/audit/changes'),
  });
}
