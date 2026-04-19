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

async function fetchOpportunities(): Promise<OpportunitiesResponse> {
  const response = await apiClient.get(API_ENDPOINT);
  return response.data as OpportunitiesResponse;
}

export function useOpportunities() {
  return useQuery({
    queryKey: ['opportunities'],
    queryFn: fetchOpportunities,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}
