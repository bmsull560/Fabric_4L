import { z } from 'zod';
import { apiClient } from './client';
import type { components, operations } from './generated/l3';
import {
  ValuePackSchema,
  ValuePackListSchema,
  type ValuePack,
} from '@/lib/schemas/valuePack';

export interface ValuePackFilters {
  industry?: string | 'all';
  status?: ValuePack['status'] | 'all';
  scope?: ValuePack['scope'] | 'all';
  category?: string | 'all';
  search?: string;
}

export interface ApplyValuePackResponse {
  success: boolean;
  message?: string;
  appliedAt?: string;
  pack_id?: string;
  entity_id?: string;
}

type PackSummaryDto = components['schemas']['PackSummary'];
type ListPacksResponse =
  operations['list_packs_v1_packs_get']['responses'][200]['content']['application/json'];
type GetPackResponse =
  operations['get_pack_v1_packs__pack_id__get']['responses'][200]['content']['application/json'];

const ApplyValuePackResponseSchema = z.object({
  success: z.boolean(),
  message: z.string().optional(),
  appliedAt: z.string().optional(),
  pack_id: z.string().optional(),
  entity_id: z.string().optional(),
});

function buildQueryString(filters: ValuePackFilters): string {
  const params = new URLSearchParams();
  if (filters.industry && filters.industry !== 'all') params.set('industry', filters.industry);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.scope && filters.scope !== 'all') params.set('scope', filters.scope);
  if (filters.category && filters.category !== 'all') params.set('category', filters.category);
  if (filters.search) params.set('search', filters.search);
  return params.toString();
}

function adaptPackSummary(dto: PackSummaryDto | GetPackResponse): ValuePack {
  const raw = dto as Record<string, unknown>;
  const candidate = {
    id: typeof raw.id === 'string' ? raw.id : dto.pack_id,
    pack_id: dto.pack_id,
    name: dto.name,
    industry: dto.industry,
    description: typeof raw.description === 'string' ? raw.description : undefined,
    driver_count: typeof raw.driver_count === 'number' ? raw.driver_count : 0,
    formula_count: typeof raw.formula_count === 'number' ? raw.formula_count : 0,
    benchmark_count: typeof raw.benchmark_count === 'number' ? raw.benchmark_count : 0,
    workflow_count: typeof raw.workflow_count === 'number' ? raw.workflow_count : 0,
    status: String(dto.status) as ValuePack['status'],
    scope: raw.scope === 'tenant' ? 'tenant' : 'global',
    updated_at: typeof raw.updated_at === 'string' ? raw.updated_at : new Date(0).toISOString(),
    created_at: typeof raw.created_at === 'string' ? raw.created_at : undefined,
    version: typeof raw.version === 'string' ? raw.version : undefined,
    owner: typeof raw.owner === 'string' ? raw.owner : undefined,
    category: typeof raw.category === 'string' ? raw.category : undefined,
  };

  return ValuePackSchema.parse(candidate);
}

export async function listValuePackSummaries(filters: ValuePackFilters): Promise<ValuePack[]> {
  const query = buildQueryString(filters);
  const path = query.length > 0 ? `/packs?${query}` : '/packs';
  const response = await apiClient.get<ListPacksResponse>('l3', path);
  const data = response.data;
  const adapted = data.map(adaptPackSummary);
  return ValuePackListSchema.parse(adapted);
}

export async function getValuePackDetail(packId: string): Promise<ValuePack> {
  const response = await apiClient.get<GetPackResponse>('l3', `/packs/${packId}`);
  return adaptPackSummary(response.data);
}

export async function applyValuePack(packId: string): Promise<ApplyValuePackResponse> {
  const response = await apiClient.post<unknown>('l3', `/packs/${packId}/apply`, {});
  return ApplyValuePackResponseSchema.parse(response.data);
}
