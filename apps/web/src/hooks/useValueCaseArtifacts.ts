import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
}

const storageKey = (accountId: string) => `value-case-artifacts:${accountId}`;

function loadArtifacts(accountId: string): ValueCaseArtifactVersion[] {
  try {
    const raw = window.localStorage.getItem(storageKey(accountId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ValueCaseArtifactVersion[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveArtifacts(accountId: string, versions: ValueCaseArtifactVersion[]) {
  window.localStorage.setItem(storageKey(accountId), JSON.stringify(versions));
}

export function useValueCaseArtifacts(accountId: string | null) {
  const queryClient = useQueryClient();
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const generateNarrative = useGenerateNarrative();

  const versionsQuery = useQuery({
    queryKey: QK.versions.detail(`value-case:${accountId ?? 'none'}`),
    queryFn: async () => {
      if (!accountId) return [];
      return loadArtifacts(accountId);
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

      const existing = loadArtifacts(input.account_id);
      const nextVersion = (existing[existing.length - 1]?.version ?? 0) + 1;

      const artifact: ValueCaseArtifactVersion = {
        id: `${input.account_id}-v${nextVersion}`,
        account_id: input.account_id,
        version: nextVersion,
        created_at: new Date().toISOString(),
        inputs: input,
        narrative: {
          id: narrative.id,
          title: narrative.title,
          sections: narrative.sections,
          created_at: narrative.created_at,
          updated_at: narrative.updated_at,
        },
        business_case: {
          summary: `Projected ${input.roi_metrics.roi} ROI with ${input.roi_metrics.payback} payback based on accepted evidence and assumptions.`,
          metrics: input.roi_metrics,
          risks: input.risk_notes,
        },
      };

      const next = [...existing, artifact];
      saveArtifacts(input.account_id, next);
      return artifact;
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
