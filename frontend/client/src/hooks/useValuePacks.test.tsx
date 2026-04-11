import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper } from "../test-utils";
import { useValuePacks, useValuePack, useApplyValuePack, ValuePackApiError } from "./useValuePacks";
import { apiClient } from "@/api/client";
import { AxiosResponse } from "axios";

// Helper to create typed mock response
const createMockResponse = <T,>(data: T): AxiosResponse<T> => ({
  data,
  status: 200,
  statusText: "OK",
  headers: {},
  config: {} as any,
});

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("useValuePacks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("useValuePacks hook", () => {
    it("should fetch value packs successfully", async () => {
      const mockPacks = [
        {
          pack_id: "pack-1",
          name: "SaaS Metrics Pack",
          industry: "SaaS / B2B",
          status: "published",
          scope: "global",
          driver_count: 5,
          formula_count: 12,
          benchmark_count: 8,
          workflow_count: 3,
          updated_at: "2024-04-01T00:00:00Z",
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockPacks));

      const { result } = renderHook(() => useValuePacks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockPacks);
    });

    it("should apply filters to API request", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse([]));

      renderHook(
        () =>
          useValuePacks({
            industry: "SaaS / B2B",
            status: "published",
            search: "metrics",
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

      expect(apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("industry=SaaS")
      );
    });

    it("should handle error states", async () => {
      const error = new ValuePackApiError("Network error", 500);
      // Clear previous mocks and set up persistent rejection
      vi.mocked(apiClient.get).mockReset().mockRejectedValue(error);

      const { result } = renderHook(() => useValuePacks(), {
        wrapper: createWrapper(),
      });

      // Wait for error state after all retries exhausted (3 retries with exponential backoff ~7s)
      await waitFor(
        () => expect(result.current.isError).toBe(true),
        { timeout: 10000 }
      );

      expect(result.current.error).toBeDefined();
      expect(result.current.error?.message).toBe("Network error");
    }, 15000);
  });

  describe("useValuePack hook (single pack)", () => {
    it("should fetch single pack by ID", async () => {
      const mockPack = {
        pack_id: "pack-1",
        name: "SaaS Metrics Pack",
        industry: "SaaS / B2B",
        status: "published",
        scope: "global",
        driver_count: 5,
        formula_count: 12,
        benchmark_count: 8,
        workflow_count: 3,
        updated_at: "2024-04-01T00:00:00Z",
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockPack));

      const { result } = renderHook(() => useValuePack("pack-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockPack);
      expect(apiClient.get).toHaveBeenCalledWith("l3", "/packs/pack-1");
    });

    it("should not fetch when packId is null", () => {
      const { result } = renderHook(() => useValuePack(null), {
        wrapper: createWrapper(),
      });

      expect(result.current.isPending).toBe(true);
      expect(result.current.fetchStatus).toBe("idle");
      expect(apiClient.get).not.toHaveBeenCalled();
    });
  });

  describe("useApplyValuePack mutation", () => {
    it("should apply pack successfully", async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce(createMockResponse({ applied: true }));

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync("pack-1");

      expect(apiClient.post).toHaveBeenCalledWith(
        "l3",
        "/packs/pack-1/apply",
        {}
      );
    });
  });
});
