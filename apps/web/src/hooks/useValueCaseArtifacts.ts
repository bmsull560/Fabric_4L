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

export type ValueCaseSourceArtifactType = "business_case" | "scenario" | "evidence" | "assumption" | "narrative" | "roi_model";

export interface ValueCaseLineageSourceRef {
  id: string;
  type: ValueCaseSourceArtifactType;
  title?: string;
  url?: string;
}

export interface ValueCaseLineagePayload {
  generated_artifact_type: "value_case" | "business_case" | "scenario";
  generated_artifact_id: string;
  source_counts: Partial<Record<ValueCaseSourceArtifactType, number>>;
  source_ids: Partial<Record<ValueCaseSourceArtifactType, string[]>>;
  source_refs: ValueCaseLineageSourceRef[];
  mutations: Array<{
    id: string;
    kind: "generation" | "regeneration" | "agent_action" | "workflow_update";
    summary: string;
    actor: string;
    created_at: string;
  }>;
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
  lineage: ValueCaseLineagePayload;
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

      const sourceRefs: ValueCaseLineageSourceRef[] = [
        { id: narrative.id, type: "narrative", title: narrative.title, url: `/narratives/${narrative.id}` },
        { id: `bc-${input.account_id}`, type: "business_case", title: `Business case for ${input.account_name}`, url: `/value-case/${input.account_id}` },
        ...input.accepted_evidence.map((item, index) => ({ id: `ev-${index + 1}`, type: "evidence" as const, title: item, url: undefined })),
        ...input.scenario_assumptions.map((item, index) => ({ id: `sc-${index + 1}`, type: "scenario" as const, title: item, url: undefined })),
      ];

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
          generated_artifact_type: "value_case",
          generated_artifact_id: `vc-${input.account_id}-${Date.now()}`,
          source_counts: {
            narrative: 1,
            business_case: 1,
            evidence: input.accepted_evidence.length,
            scenario: input.scenario_assumptions.length,
          },
          source_ids: {
            narrative: [narrative.id],
            business_case: [`bc-${input.account_id}`],
            evidence: sourceRefs.filter((item) => item.type === "evidence").map((item) => item.id),
            scenario: sourceRefs.filter((item) => item.type === "scenario").map((item) => item.id),
          },
          source_refs: sourceRefs,
          mutations: [
            {
              id: `mut-${Date.now()}`,
              kind: "generation",
              summary: `Generated value case from ${sourceRefs.length} linked artifacts`,
              actor: "ValuePilot",
              created_at: new Date().toISOString(),
            },
          ],
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
