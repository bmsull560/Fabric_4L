import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper } from "../test-utils";
import { apiClient } from "@/api/client";
import { useROIScenarioVersions } from "./useROIScenarios";

vi.mock("@/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}));

describe("useROIScenarioVersions", () => {
  beforeEach(() => vi.clearAllMocks());

  it("reload/resume returns latest backend versions for scoped case/model", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: { items: [{ versionId: "sv_2", accountId: "acc-1", caseId: "case-1", modelId: "mdl-1", name: "Latest", assumptions: { deal_size: 1, implementation_cost: 1, annual_benefit: 1, time_horizon_years: 1, discount_rate: 1, ramp_months: 1 }, updatedAt: "2026-05-07T00:00:00Z" }] },
    });

    const { result } = renderHook(
      () => useROIScenarioVersions({ tenantId: "tenant-1", accountId: "acc-1", caseId: "case-1", modelId: "mdl-1" }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].name).toBe("Latest");
    expect(apiClient.get).toHaveBeenCalledWith(
      "l4",
      "/analysis/cases/case-1/workspace/value-model/scenarios?account_id=acc-1&model_id=mdl-1"
    );
  });

  it("cross-session retrieval refetches server data in a new query client session", async () => {
    (apiClient.get as Mock)
      .mockResolvedValueOnce({ data: { items: [{ versionId: "sv_a", accountId: "acc-1", caseId: "case-1", modelId: "mdl-1", name: "Session A", assumptions: { deal_size: 2, implementation_cost: 2, annual_benefit: 2, time_horizon_years: 2, discount_rate: 2, ramp_months: 2 }, updatedAt: "2026-05-07T00:00:00Z" }] } })
      .mockResolvedValueOnce({ data: { items: [{ versionId: "sv_b", accountId: "acc-1", caseId: "case-1", modelId: "mdl-1", name: "Session B", assumptions: { deal_size: 3, implementation_cost: 3, annual_benefit: 3, time_horizon_years: 3, discount_rate: 3, ramp_months: 3 }, updatedAt: "2026-05-07T01:00:00Z" }] } });

    const first = renderHook(() => useROIScenarioVersions({ accountId: "acc-1", caseId: "case-1", modelId: "mdl-1" }), { wrapper: createWrapper() });
    await waitFor(() => expect(first.result.current.isSuccess).toBe(true));

    const second = renderHook(() => useROIScenarioVersions({ accountId: "acc-1", caseId: "case-1", modelId: "mdl-1" }), { wrapper: createWrapper() });
    await waitFor(() => expect(second.result.current.isSuccess).toBe(true));

    expect(first.result.current.data?.[0].name).toBe("Session A");
    expect(second.result.current.data?.[0].name).toBe("Session B");
    expect(apiClient.get).toHaveBeenCalledTimes(2);
  });
});
