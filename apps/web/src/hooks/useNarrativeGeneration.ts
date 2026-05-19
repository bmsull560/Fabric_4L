/**
 * useNarrativeGeneration — orchestrates narrative creation via Layer 4 workflows
 *
 * Maps UI actions to backend capabilities:
 *   Output types → workflow_type:
 *     narrative       → business_case   (NarrativeSynthesisAgent)
 *     roi_model       → roi_calculator  (ROICalculationAgent)
 *     value_template  → business_case   (with template config)
 *
 *   Input methods → Layer 1 / Layer 4:
 *     text   → direct workflow submission
 *     import → L1 ingestion (URL submission)
 *     file   → L1 file ingestion
 *     crm    → L4 account sync
 *
 *   Industry → Layer 6 benchmarks context
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/api/typedClient';
import type { l4, l6 } from '@/api/generated';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import type { OutputType } from '@/stores/narrativeStore';

// ── Types ────────────────────────────────────────────────────────────────────

export interface NarrativeGenerationRequest {
  prompt: string;
  outputType: OutputType;
  industry: string;
  benchmarkDatasetIds?: string[];
}

export interface NarrativeGenerationResponse {
  workflow_id: string;
  status: 'submitted' | 'pending';
  message: string;
}

type WorkflowCreateResponse = {
  workflow_instance_id?: string;
  workflow_id?: string;
};

// ── Workflow type mapping ─────────────────────────────────────────────────────

const OUTPUT_TYPE_TO_WORKFLOW: Record<OutputType, string> = {
  narrative: 'business_case',
  roi_model: 'roi_calculator',
  value_template: 'business_case',
};

// ── Hooks ────────────────────────────────────────────────────────────────────

/**
 * Fetch available industries from Layer 6 benchmarks.
 * Cached for 10 minutes since industries rarely change.
 */
export function useIndustries() {
  return useQuery<string[]>({
    queryKey: QK.benchmarks.industries(),
    queryFn: async () => {
      const response = await apiGet<string[] | { industries?: string[] }>('l6', '/industries');
      const data = response.data;
      if (Array.isArray(data)) return data;
      if (data.industries && Array.isArray(data.industries)) return data.industries;
      return [];
    },
    staleTime: STALE_TIME.reference,
  });
}

/**
 * Submit a narrative generation workflow to Layer 4.
 * Creates the appropriate workflow type based on the selected output type.
 */
export function useGenerateNarrative() {
  const queryClient = useQueryClient();

  return useMutation<NarrativeGenerationResponse, Error, NarrativeGenerationRequest>({
    mutationFn: async ({ prompt, outputType, industry, benchmarkDatasetIds }) => {
      const workflowType = OUTPUT_TYPE_TO_WORKFLOW[outputType];

      const response = await apiPost<l4.components['schemas']['WorkflowCreateResponse'] & { workflow_id?: string }>('l4', '/workflows', {
        workflow_type: workflowType,
        inputs: {
          custom_data: {
            prompt,
            industry,
            output_type: outputType,
            sections: outputType === 'narrative'
              ? ['executive_summary', 'current_state', 'proposed_solution', 'roi_analysis', 'implementation', 'next_steps']
              : undefined,
            benchmark_dataset_ids: benchmarkDatasetIds,
          },
        },
      });

      const workflowId = response.data.workflow_instance_id || response.data.workflow_id;
      if (!workflowId) {
        throw new Error('Workflow creation response missing workflow id');
      }

      return {
        workflow_id: String(workflowId),
        status: 'submitted',
        message: `${outputType} generation started`,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.workflows.active() });
      queryClient.invalidateQueries({ queryKey: QK.workflows.history() });
    },
  });
}
