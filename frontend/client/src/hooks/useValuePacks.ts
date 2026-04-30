import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG, formatZodError } from './useApiShared';
import {
  ValuePackSchema,
  ValuePackListSchema,
  type ValuePack,
  type PackStatus,
  type PackScope,
} from '@/lib/schemas/valuePack';

// Domain-specific error class
export class ValuePackApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'ValuePackApiError';
  }
}

// Re-export types from schema for backward compatibility
export type { ValuePack, PackStatus, PackScope };


export interface ValuePackFilters {
  industry?: string | 'all';
  status?: PackStatus | 'all';
  scope?: PackScope | 'all';
  category?: string | 'all';
  search?: string;
}

/**
 * Fetch value packs with optional filtering.
 * @param filters - Optional filters for industry, status, scope, category, or search
 * @returns Array of value packs matching the filters
 */
async function fetchValuePacks(filters: ValuePackFilters): Promise<ValuePack[]> {
  const params = new URLSearchParams();
  if (filters.industry && filters.industry !== 'all') params.set('industry', filters.industry);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.scope && filters.scope !== 'all') params.set('scope', filters.scope);
  if (filters.category && filters.category !== 'all') params.set('category', filters.category);
  if (filters.search) params.set('search', filters.search);

  const response = await apiClient.get('l3', `/packs?${params.toString()}`);

  // Runtime validation with Zod
  const parsed = ValuePackListSchema.safeParse((response as any).data);
  if (!parsed.success) {
    console.error('Value pack list validation failed:', parsed.error);
    throw new ValuePackApiError(formatZodError(parsed.error, 'value pack list response'));
  }
  return parsed.data;
}

/**
 * Hook to fetch a list of value packs with optional filtering.
 * Results are cached for 1 minute (STALE_TIME.stats).
 *
 * @param filters - Optional filters for industry, status, scope, category, or search term
 * @returns React Query result with array of ValuePack objects
 *
 * @example
 * const { data: packs, isLoading } = useValuePacks({ industry: 'SaaS / B2B', status: 'published' });
 */
export function useValuePacks(filters: ValuePackFilters = {}) {
  return useQuery<ValuePack[], ValuePackApiError>({
    queryKey: QK.valuePacks.list(filters),
    queryFn: () => withApiError(fetchValuePacks(filters), ValuePackApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Fetch a single value pack by ID.
 * @param packId - The unique identifier of the value pack
 * @returns The value pack details
 * @throws ValuePackApiError if the pack is not found or request fails
 */
async function fetchValuePack(packId: string): Promise<ValuePack> {
  const response = await apiClient.get('l3', `/packs/${packId}`);

  // Runtime validation with Zod
  const parsed = ValuePackSchema.safeParse((response as any).data);
  if (!parsed.success) {
    console.error('Value pack detail validation failed:', parsed.error);
    throw new ValuePackApiError(formatZodError(parsed.error, 'value pack response'));
  }
  return parsed.data;
}

/**
 * Hook to fetch a single value pack by ID.
 *
 * @param packId - The pack ID to fetch, or null to disable the query
 * @returns Query result with ValuePack data and loading/error states
 */
export function useValuePack(packId: string | null) {
  return useQuery<ValuePack, ValuePackApiError>({
    queryKey: QK.valuePacks.detail(packId || ''),
    queryFn: () => withApiError(fetchValuePack(packId!), ValuePackApiError),
    enabled: !!packId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/** Parameters for applying/deploying a value pack */
export interface ApplyValuePackParams {
  packId: string;
}

export interface ApplyValuePackResponse {
  success: boolean;
  message?: string;
}

/**
 * Hook to apply/deploy a value pack to the current tenant.
 * Invalidates the value packs list query on success.
 *
 * @returns Mutation object with typed data/error/parameter types
 */
export function useApplyValuePack() {
  const queryClient = useQueryClient();

  return useMutation<ApplyValuePackResponse, ValuePackApiError, ApplyValuePackParams>({
    mutationFn: async ({ packId }) => {
      if (!packId) throw new ValuePackApiError('Pack ID is required');
      const response = await apiClient.post('l3', `/packs/${packId}/apply`, {});
      return (response as { data: unknown }).data as ApplyValuePackResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.valuePacks.all });
    },
    onError: (error) => {
      // Log error for monitoring/debugging; UI handles display via error state
      if (process.env.NODE_ENV === 'development') {
        console.error('[useApplyValuePack] Deployment failed:', error.message);
      }
    },
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// ValuePack Framework v1.0 - Industry-Specific Value Model Templates
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * ValuePack Framework Industry Data
 */
export interface ValuePackFrameworkData {
  industry_id: string;
  display_name: string;
  tier: 1 | 2 | 3;
  description: string;
  primary_value_drivers: Array<{
    id: string;
    name: string;
    description: string;
    typical_impact: string;
    measurement_approach: string;
  }>;
  core_use_cases: Array<{
    id: string;
    name: string;
    description: string;
    target_persona: string;
    business_problem: string;
  }>;
  economic_model_types: Array<{
    id: string;
    name: string;
    formula_shape: string;
    inputs: string[];
    output_unit: string;
    typical_range?: string;
  }>;
  why_it_wins: Array<{
    statement: string;
    differentiation: string;
    proof_point: string;
  }>;
  composable_model_templates: Array<{
    template_id: string;
    template_name: string;
    formula_pattern: string;
    applicable_industries: string[];
    example_calculation: string;
  }>;
  pre_wired_ontology_tags: Array<{
    tag: string;
    category: string;
    related_tags: string[];
  }>;
  metadata: {
    deal_size_range: string;
    sales_cycle_length: string;
    switching_cost: 'low' | 'medium' | 'high';
    data_richness: 'low' | 'medium' | 'high';
    feedback_loop_speed: 'slow' | 'medium' | 'fast';
  };
  completeness_score?: number;
  proof_requirements?: Array<{
    id: string;
    requirement: string;
    evidence_type: string;
  } | null>;
}

/**
 * Fetch ValuePack Framework data for all industries.
 */
async function fetchValuePackFrameworkList(tier?: number, search?: string): Promise<ValuePackFrameworkData[]> {
  const params = new URLSearchParams();
  if (tier) params.set('tier', String(tier));
  if (search) params.set('search', search);
  
  const response = await apiClient.get('l3', `/valuepacks?${params.toString()}`) as { data: { items: ValuePackFrameworkData[] } };
  return response.data.items;
}

/**
 * Hook to list ValuePacks with Framework v1.0 schema.
 */
export function useValuePackFrameworkList(tier?: number, search?: string) {
  return useQuery<ValuePackFrameworkData[], ValuePackApiError>({
    queryKey: [...QK.valuePacks.all, 'framework', 'list', tier, search],
    queryFn: () => withApiError(fetchValuePackFrameworkList(tier, search), ValuePackApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
  });
}

/**
 * Fetch single ValuePack Framework data.
 */
async function fetchValuePackFramework(industryId: string): Promise<ValuePackFrameworkData> {
  const response = await apiClient.get('l3', `/valuepacks/${industryId}`) as { data: ValuePackFrameworkData };
  return response.data;
}

/**
 * Hook to get a single ValuePack Framework v1.0 data.
 */
export function useValuePackFramework(industryId: string | null) {
  return useQuery<ValuePackFrameworkData, ValuePackApiError>({
    queryKey: [...QK.valuePacks.all, 'framework', 'detail', industryId],
    queryFn: () => withApiError(fetchValuePackFramework(industryId!), ValuePackApiError),
    enabled: !!industryId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
  });
}

/**
 * Cross-industry ontology map.
 */
export interface OntologyMapData {
  shared_drivers: Array<{
    id: string;
    name: string;
    industries: string[];
    count: number;
  }>;
  shared_model_types: Array<{
    id: string;
    name: string;
    industries: string[];
    count: number;
  }>;
  shared_proof_patterns: Array<{
    id: string;
    requirement: string;
    industries: string[];
    count: number;
  }>;
  cross_reference_matrix: Record<string, Record<string, number>>;
}

/**
 * Hook to get cross-industry ontology map.
 */
export function useValuePackOntologyMap() {
  return useQuery<OntologyMapData, ValuePackApiError>({
    queryKey: [...QK.valuePacks.all, 'framework', 'ontology'],
    queryFn: async () => {
      const response = await apiClient.get('l3', '/valuepacks/ontology-map') as { data: OntologyMapData };
      return response.data;
    },
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
  });
}

/**
 * Composable template library.
 */
export interface TemplateLibraryData {
  templates: ValuePackFrameworkData['composable_model_templates'];
  template_usage: Record<string, string[]>;
}

/**
 * Hook to get composable template library.
 */
export function useValuePackTemplates() {
  return useQuery<TemplateLibraryData, ValuePackApiError>({
    queryKey: [...QK.valuePacks.all, 'framework', 'templates'],
    queryFn: async () => {
      const response = await apiClient.get('l3', '/valuepacks/composable-templates') as { data: TemplateLibraryData };
      return response.data;
    },
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
  });
}

/**
 * ValuePack comparison request/response.
 */
export interface ValuePackComparisonRequest {
  industry_ids: string[];
  dimensions?: string[];
}

export interface ValuePackComparisonData {
  valuepacks: ValuePackFrameworkData[];
  comparison_matrix: Record<string, Record<string, string[] | string>>;
  shared_templates: string[];
  differentiation_analysis: Record<string, string>;
}

/**
 * Hook to compare multiple ValuePacks.
 */
export function useValuePackComparison() {
  return useMutation<ValuePackComparisonData, ValuePackApiError, ValuePackComparisonRequest>({
    mutationFn: async (request) => {
      const response = await apiClient.post('l3', '/valuepacks/compare', request) as { data: ValuePackComparisonData };
      return response.data;
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('[useValuePackComparison] Comparison failed:', error.message);
      }
    },
  });
}

/**
 * Suggest ValuePacks based on prospect profile.
 */
export interface ProspectProfile {
  industry?: string;
  sub_industry?: string;
  employee_count?: number;
  annual_revenue?: string;
  pain_points?: string[];
  current_tech_stack?: string[];
}

export interface ValuePackSuggestion {
  industry_id: string;
  display_name: string;
  match_score: number;
  match_breakdown: {
    industry_match: number;
    pain_point_alignment: number;
    size_compatibility: number;
    tech_fit: number;
  };
  recommended_drivers: Array<{
    driver_id: string;
    relevance: string;
  }>;
}

/**
 * Hook to suggest ValuePacks for a prospect.
 */
export function useSuggestValuePacks() {
  // For now, this is a local calculation based on available data
  // In the future, this could call an agent endpoint
  const { data: allValuePacks } = useValuePackFrameworkList();
  
  return {
    suggest: (profile: ProspectProfile): ValuePackSuggestion[] => {
      if (!allValuePacks) return [];
      
      // Simple matching algorithm
      return allValuePacks.map(vp => {
        let industryMatch = 0;
        let painPointAlignment = 0;
        
        // Industry match
        if (profile.industry) {
          const profileInd = profile.industry.toLowerCase();
          const vpInd = vp.industry_id.toLowerCase();
          if (vpInd.includes(profileInd) || profileInd.includes(vpInd.replace('_', ' '))) {
            industryMatch = 1.0;
          } else {
            // Check ontology tags
            const hasRelatedTag = vp.pre_wired_ontology_tags.some(tag => 
              tag.related_tags.some(rt => profileInd.includes(rt.toLowerCase()))
            );
            if (hasRelatedTag) industryMatch = 0.7;
          }
        }
        
        // Pain point alignment
        if (profile.pain_points) {
          const matchedDrivers = vp.primary_value_drivers.filter(driver =>
            profile.pain_points!.some(pp => 
              driver.name.toLowerCase().includes(pp.toLowerCase()) ||
              driver.description.toLowerCase().includes(pp.toLowerCase())
            )
          );
          painPointAlignment = Math.min(matchedDrivers.length * 0.25, 1.0);
        }
        
        const matchScore = (industryMatch * 0.4) + (painPointAlignment * 0.3) + 0.3;
        
        return {
          industry_id: vp.industry_id,
          display_name: vp.display_name,
          match_score: matchScore,
          match_breakdown: {
            industry_match: industryMatch,
            pain_point_alignment: painPointAlignment,
            size_compatibility: 0.8, // Default
            tech_fit: 1.0, // Default
          },
          recommended_drivers: vp.primary_value_drivers
            .filter(d => profile.pain_points?.some(pp => 
              d.description.toLowerCase().includes(pp.toLowerCase())
            ))
            .map(d => ({ driver_id: d.id, relevance: `Matches pain point` })),
        };
      }).sort((a, b) => b.match_score - a.match_score);
    },
    isReady: !!allValuePacks,
  };
}
