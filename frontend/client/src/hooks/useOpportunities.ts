/**
 * useOpportunities Hook — Real API Integration
 *
 * Fetches opportunity data from Layer 4 Discover API.
 * Replaces previous MOCK_OPPORTUNITIES hardcoded data.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export type OpportunityStatus = 'new' | 'investigating' | 'qualified' | 'converted' | 'dismissed';
export type ImpactLevel = 'high' | 'medium' | 'low';

export interface Opportunity {
  id: string;
  title: string;
  description: string;
  account: string;
  accountId: string;
  category: string;
  status: OpportunityStatus;
  impact: ImpactLevel;
  estimatedValue: string;
  confidenceScore: number;
  aiScore: number;
  discoveredAt: string;
  insights: string[];
  recommendedActions: string[];
  sources: string[];
}

export interface OpportunitiesResponse {
  opportunities: Opportunity[];
  total: number;
  generatedAt: string;
}

const API_ENDPOINT = '/v1/discover/opportunities';
const STALE_TIME_MS = 5 * 60 * 1000; // 5 minutes
const MAX_RETRIES = 2;

export class OpportunitiesApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly response?: unknown
  ) {
    super(message);
    this.name = 'OpportunitiesApiError';
  }
}

async function fetchOpportunities(): Promise<OpportunitiesResponse> {
  const response = await apiClient.get<OpportunitiesResponse>(API_ENDPOINT);

  if (!response.data || typeof response.data !== 'object') {
    throw new OpportunitiesApiError('Invalid response format from API');
  }

  // Validate required fields
  const data = response.data;
  if (!Array.isArray(data.opportunities)) {
    throw new OpportunitiesApiError('Missing or invalid opportunities array');
  }

  return data;
}

export function useOpportunities() {
  return useQuery<OpportunitiesResponse, OpportunitiesApiError>({
    queryKey: ['opportunities'],
    queryFn: fetchOpportunities,
    staleTime: STALE_TIME_MS,
    retry: MAX_RETRIES,
  });
}
