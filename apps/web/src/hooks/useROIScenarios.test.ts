import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper } from "../test-utils";
import { apiClient } from "@/api/client";
import { useROIScenarioVersions, useSaveROIScenarioVersion, DEFAULT_SCENARIO_ASSUMPTIONS, validateScenarioAssumptions } from "./useROIScenarios";

vi.mock("@/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}));

describe("useROIScenarioVersions", () => {
  beforeEach(() => vi.clearAllMocks());

  it("reload/resume returns latest backend versions for scoped case/model", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: { items: [{ versionId: "sv_2", accountId: "acc-1", caseId: "case-1", modelId: "mdl-1", name: "Latest", assumptions: DEFAULT_SCENARIO_ASSUMPTIONS, updatedAt: "2026-05-07T00:00:00Z" }] },
    });

    const { result } = renderHook(
      () => useROIScenarioVersions({ tenantId: "tenant-1", accountId: "acc-1", caseId: "case-1", modelId: "mdl-1" }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].name).toBe("Latest");
  });

  it("scenario validation is deterministic for identical assumptions", () => {
    const a = validateScenarioAssumptions(DEFAULT_SCENARIO_ASSUMPTIONS);
    const b = validateScenarioAssumptions(DEFAULT_SCENARIO_ASSUMPTIONS);
    expect(a).toEqual(b);
  });

  it("round-trip persistence sends scenario assumptions for all variants", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: { versionId: "sv_3" } });
    const { result } = renderHook(
      () => useSaveROIScenarioVersion({ accountId: "acc-1", caseId: "case-1", modelId: "mdl-1" }, DEFAULT_SCENARIO_ASSUMPTIONS),
      { wrapper: createWrapper() }
    );

    await result.current.mutateAsync("v1");
    expect(apiClient.post).toHaveBeenCalledTimes(1);
    expect((apiClient.post as Mock).mock.calls[0]?.[0]).toBe("l4");
    expect((apiClient.post as Mock).mock.calls[0]?.[1]).toBe("/analysis/cases/case-1/workspace/value-model/scenarios");
    expect((apiClient.post as Mock).mock.calls[0]?.[2]).toEqual(expect.objectContaining({ assumptions: DEFAULT_SCENARIO_ASSUMPTIONS }));
  });
});
