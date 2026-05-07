import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { QK } from "@/hooks/queryKeys";

export type ScenarioState = {
  deal_size: number;
  implementation_cost: number;
  annual_benefit: number;
  time_horizon_years: number;
  discount_rate: number;
  ramp_months: number;
};

export type PersistedScenarioVersion = {
  versionId: string;
  accountId: string;
  caseId: string;
  modelId: string;
  name: string;
  assumptions: ScenarioState;
  updatedAt: string;
};

type Scope = { tenantId?: string | null; accountId?: string | null; caseId?: string | null; modelId?: string | null };

function scopeReady(scope: Scope): scope is Required<Pick<Scope, "accountId" | "caseId" | "modelId">> & Scope {
  return Boolean(scope.accountId && scope.caseId && scope.modelId);
}

export function useROIScenarioVersions(scope: Scope) {
  return useQuery<PersistedScenarioVersion[]>({
    queryKey: QK.roi.scenarioVersions(scope),
    enabled: scopeReady(scope),
    queryFn: async () => {
      const response = await apiClient.get(
        "l4",
        `/analysis/cases/${encodeURIComponent(scope.caseId ?? "")}/workspace/value-model/scenarios?account_id=${encodeURIComponent(scope.accountId ?? "")}&model_id=${encodeURIComponent(scope.modelId ?? "")}`
      );
      return (response.data?.items ?? response.data ?? []) as PersistedScenarioVersion[];
    },
  });
}

export function useSaveROIScenarioVersion(scope: Scope, scenario: ScenarioState) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: ["roi", "scenario", "save", scope.accountId ?? "", scope.caseId ?? "", scope.modelId ?? ""],
    mutationFn: async (name: string) => {
      const response = await apiClient.post("l4", `/analysis/cases/${encodeURIComponent(scope.caseId ?? "")}/workspace/value-model/scenarios`, {
        account_id: scope.accountId,
        model_id: scope.modelId,
        name,
        assumptions: scenario,
      });
      return response.data as PersistedScenarioVersion;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QK.roi.scenarioVersions(scope) });
    },
  });
}

export function useUpdateROIScenarioVersion(scope: Scope) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: ["roi", "scenario", "update", scope.accountId ?? "", scope.caseId ?? "", scope.modelId ?? ""],
    mutationFn: async ({ versionId, assumptions }: { versionId: string; assumptions: ScenarioState }) => {
      const response = await apiClient.patch("l4", `/analysis/cases/${encodeURIComponent(scope.caseId ?? "")}/workspace/value-model/scenarios/${encodeURIComponent(versionId)}`, {
        account_id: scope.accountId,
        model_id: scope.modelId,
        assumptions,
      });
      return response.data as PersistedScenarioVersion;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QK.roi.scenarioVersions(scope) });
    },
  });
}
