import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import {
  parseBusinessCaseNarrativeOutput,
  parseBusinessCaseRoiOutput,
  parseWorkflowResult,
  type ApiWorkflowStepDto,
} from '@/types/api';

export interface UseCase {
  name: string;
  persona: string;
  driver: string;
  roi: string;
  payback: string;
  confidence: number;
}

export interface BusinessCaseData {
  id: string;
  company: string;
  totalValue: string;
  useCases: UseCase[];
  avgPayback: string;
  confidence: number;
  executiveSummary: string;
  generatedAt: string;
}

const BUSINESS_CASE_KEYS = {
  all: ['business-cases'] as const,
  detail: (id: string) => [...BUSINESS_CASE_KEYS.all, 'detail', id] as const,
};

/**
 * Get business case from L4 agent workflow results
 * Note: This queries the L4 workflow results for business_case type workflows
 */
export function useBusinessCase(caseId: string | null) {
  return useQuery({
    queryKey: BUSINESS_CASE_KEYS.detail(caseId || ''),
    queryFn: async () => {
      if (!caseId) throw new Error('No case ID provided');

      // Query L4 for workflow result
      const response = await apiClient.get('l4', `/workflows/${caseId}/result`);
      const result = parseWorkflowResult(response.data);

      // Parse workflow output into business case format
      const output = result.output || {};
      const steps = result.steps || [];

      // Extract data from workflow steps
      const findAgentStep = (agentName: string): ApiWorkflowStepDto | undefined =>
        steps.find((step) => step.agent === agentName);
      const roiResult = parseBusinessCaseRoiOutput(findAgentStep('ROICalculationAgent')?.result?.output);
      const narrativeResult = parseBusinessCaseNarrativeOutput(findAgentStep('NarrativeSynthesisAgent')?.result?.output);

      // Map use cases
      const useCases: UseCase[] = (roiResult.use_cases || []).map((uc) => ({
        name: uc.name || 'Unknown Use Case',
        persona: uc.persona || 'Unknown',
        driver: uc.value_driver || 'Unknown',
        roi: formatCurrency(uc.roi_value ?? 0),
        payback: `${uc.payback_months ?? 12} mo`,
        confidence: Math.round((uc.confidence ?? 0.8) * 100),
      }));

      // Calculate totals
      const totalValue = roiResult.total_value ?? 0;
      const avgPayback = roiResult.avg_payback_months ?? 12;
      const confidence = Math.round((roiResult.confidence ?? 0.85) * 100);

      return {
        id: caseId,
        company: output.company_name || 'Acme Corp',
        totalValue: formatCurrency(totalValue),
        useCases,
        avgPayback: `${avgPayback} months`,
        confidence,
        executiveSummary: narrativeResult.executive_summary || generateSummary(useCases, totalValue),
        generatedAt: result.completed_at || new Date().toISOString(),
      };
    },
    enabled: !!caseId,
    staleTime: 60 * 1000,
  });
}

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value}`;
}

function generateSummary(useCases: UseCase[], totalValue: number): string {
  if (useCases.length === 0) {
    return 'No use cases available for analysis.';
  }

  const topCase = useCases[0];
  return `${topCase.name} presents the most significant opportunity with an estimated ${topCase.roi} in value. Combined with other identified use cases, the total addressable value is estimated at ${formatCurrency(totalValue)} annually with an average payback period of ${useCases.length > 1 ? 'several months' : '6-9 months'}.`;
}
