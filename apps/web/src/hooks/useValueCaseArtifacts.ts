import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/api/typedClient';
import type { l4 } from '@/api/generated';
import { QK } from './queryKeys';
import { useGenerateNarrative, type Narrative } from './useNarratives';

export interface ValueCaseArtifactsInput {
  account_id: string;
  account_name: string;
  stakeholders: string[];
  accepted_evidence: string[];
  scenario_assumptions: string[];
  roi_metrics: {
    three_year_value: string;
    roi: string;
    payback: string;
  };
  risk_notes: string[];
}

export interface ValueCaseArtifactVersion {
  id: string;
  account_id: string;
  version: number;
  created_at: string;
  inputs: ValueCaseArtifactsInput;
  narrative: Pick<Narrative, 'id' | 'title' | 'sections' | 'created_at' | 'updated_at'>;
  business_case: {
    summary: string;
    metrics: ValueCaseArtifactsInput['roi_metrics'];
    risks: string[];
  };
  lineage: {
    narrative_id: string;
    business_case_id: string;
  };
}

export function useValueCaseArtifacts(accountId: string | null) {
  const queryClient = useQueryClient();
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const generateNarrative = useGenerateNarrative();

  const versionsQuery = useQuery({
    queryKey: QK.versions.detail(`value-case:${accountId ?? 'none'}`),
    queryFn: async () => {
      if (!accountId) return [];
      const response = await apiGet<{ versions?: ValueCaseArtifactVersion[] }>('l4', `/v1/value-case/artifacts?account_id=${encodeURIComponent(accountId)}`);
      return response.data.versions ?? [];
    },
    enabled: Boolean(accountId),
  });

  const selectedVersion = useMemo(() => {
    const versions = versionsQuery.data ?? [];
    if (!versions.length) return null;
    if (!selectedVersionId) return versions[versions.length - 1] ?? null;
    return versions.find((item) => item.id === selectedVersionId) ?? null;
  }, [versionsQuery.data, selectedVersionId]);

  const generateArtifact = useMutation({
    mutationFn: async (input: ValueCaseArtifactsInput) => {
      const narrative = await generateNarrative.mutateAsync({
        account_id: input.account_id,
        title: `Value case narrative — ${input.account_name}`,
        audience: 'evaluation_committee',
        tone: 'financial',
        sections: ['executive_summary', 'stakeholder_mapping', 'roi_overview', 'risk_and_mitigation'],
      });

      const response = await apiPost<ValueCaseArtifactVersion>('l4', '/v1/value-case/artifacts', {
        account_id: input.account_id,
        inputs: input,
        narrative: {
          id: narrative.id,
          title: narrative.title,
          sections: narrative.sections,
          created_at: narrative.created_at,
          updated_at: narrative.updated_at,
        },
        lineage: {
          narrative_id: narrative.id,
          business_case_id: `bc-${input.account_id}`,
        },
      });
      return response.data;
    },
    onSuccess: (artifact) => {
      setSelectedVersionId(artifact.id);
      queryClient.invalidateQueries({ queryKey: QK.versions.detail(`value-case:${artifact.account_id}`) });
    },
  });

  return {
    versions: versionsQuery.data ?? [],
    isLoadingVersions: versionsQuery.isLoading,
    selectedVersion,
    setSelectedVersionId,
    generateArtifact,
  };
}
