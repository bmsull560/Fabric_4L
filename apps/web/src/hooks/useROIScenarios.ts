import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPatch } from "@/api/typedClient";
import type { l4 } from "@/api/generated";
import { QK } from "@/hooks/queryKeys";

export type ScenarioState = {
  deal_size: number;
  implementation_cost: number;
  annual_benefit: number;
  time_horizon_years: number;
  discount_rate: number;
  ramp_months: number;
};

export type ScenarioName = "conservative" | "expected" | "optimistic";

export type ScenarioAssumptionSet = Record<ScenarioName, ScenarioState>;

export const DEFAULT_SCENARIO_ASSUMPTIONS: ScenarioAssumptionSet = {
  conservative: { deal_size: 100000, implementation_cost: 70000, annual_benefit: 80000, time_horizon_years: 3, discount_rate: 11, ramp_months: 5 },
  expected: { deal_size: 120000, implementation_cost: 60000, annual_benefit: 100000, time_horizon_years: 3, discount_rate: 10, ramp_months: 3 },
  optimistic: { deal_size: 140000, implementation_cost: 50000, annual_benefit: 120000, time_horizon_years: 3, discount_rate: 9, ramp_months: 2 },
};

export function validateScenarioAssumptions(bundle: ScenarioAssumptionSet): string[] {
  const errors: string[] = [];
  for (const [name, assumptions] of Object.entries(bundle) as Array<[ScenarioName, ScenarioState]>) {
    if (assumptions.deal_size <= 0) errors.push(`${name}: deal_size must be > 0`);
    if (assumptions.implementation_cost < 0) errors.push(`${name}: implementation_cost must be >= 0`);
    if (assumptions.annual_benefit < 0) errors.push(`${name}: annual_benefit must be >= 0`);
    if (assumptions.time_horizon_years <= 0) errors.push(`${name}: time_horizon_years must be > 0`);
    if (assumptions.discount_rate < 0 || assumptions.discount_rate > 100) errors.push(`${name}: discount_rate must be between 0 and 100`);
    if (assumptions.ramp_months < 0 || assumptions.ramp_months > assumptions.time_horizon_years * 12) errors.push(`${name}: ramp_months must be within the time horizon`);
  }
  if (bundle.conservative.annual_benefit > bundle.expected.annual_benefit || bundle.expected.annual_benefit > bundle.optimistic.annual_benefit) {
    errors.push("annual_benefit must be conservative <= expected <= optimistic");
  }
  if (bundle.conservative.implementation_cost < bundle.expected.implementation_cost || bundle.expected.implementation_cost < bundle.optimistic.implementation_cost) {
    errors.push("implementation_cost must be conservative >= expected >= optimistic");
  }
  return errors;
}

export type PersistedScenarioVersion = {
  versionId: string;
  accountId: string;
  caseId: string;
  modelId: string;
  name: string;
  assumptions: ScenarioAssumptionSet;
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
      const response = await apiGet<{ items?: PersistedScenarioVersion[] } | PersistedScenarioVersion[]>(
        "l4",
        `/analysis/cases/${encodeURIComponent(scope.caseId ?? "")}/workspace/value-model/scenarios?account_id=${encodeURIComponent(scope.accountId ?? "")}&model_id=${encodeURIComponent(scope.modelId ?? "")}`
      );
      const data = response.data;
      return Array.isArray(data) ? data : data.items ?? [];
    },
  });
}

export function useSaveROIScenarioVersion(scope: Scope, scenario: ScenarioAssumptionSet) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: ["roi", "scenario", "save", scope.accountId ?? "", scope.caseId ?? "", scope.modelId ?? ""],
    mutationFn: async (name: string) => {
      const validationErrors = validateScenarioAssumptions(scenario);
      if (validationErrors.length) throw new Error(validationErrors.join("; "));
      const response = await apiPost<PersistedScenarioVersion>("l4", `/analysis/cases/${encodeURIComponent(scope.caseId ?? "")}/workspace/value-model/scenarios`, {
        account_id: scope.accountId,
        model_id: scope.modelId,
        name,
        assumptions: scenario,
      });
      return response.data;
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
    mutationFn: async ({ versionId, assumptions }: { versionId: string; assumptions: ScenarioAssumptionSet }) => {
      const validationErrors = validateScenarioAssumptions(assumptions);
      if (validationErrors.length) throw new Error(validationErrors.join("; "));
      const response = await apiPatch<PersistedScenarioVersion>("l4", `/analysis/cases/${encodeURIComponent(scope.caseId ?? "")}/workspace/value-model/scenarios/${encodeURIComponent(versionId)}`, {
        account_id: scope.accountId,
        model_id: scope.modelId,
        assumptions,
      });
      return response.data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QK.roi.scenarioVersions(scope) });
    },
  });
}
