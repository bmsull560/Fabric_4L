import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { useValuePacks, useValuePack, useApplyValuePack } from "./useValuePacks";
import * as apiClientModule from "@/api/client";

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
};

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

      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
        data: mockPacks,
      });

      const { result } = renderHook(() => useValuePacks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockPacks);
    });

    it("should apply filters to API request", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
        data: [],
      });

      const { result } = renderHook(
        () =>
          useValuePacks({
            industry: "SaaS / B2B",
            status: "published",
            search: "metrics",
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("industry=SaaS+%2F+B2B")
      );
      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("status=published")
      );
      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("search=metrics")
      );
    });

    it("should handle error states", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Network error")
      );

      const { result } = renderHook(() => useValuePacks(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
      expect(result.current.error?.message).toBe("Network error");
    });
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

      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
        data: mockPack,
      });

      const { result } = renderHook(() => useValuePack("pack-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockPack);
      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        "/packs/pack-1"
      );
    });

    it("should not fetch when packId is null", async () => {
      const { result } = renderHook(() => useValuePack(null), {
        wrapper: createWrapper(),
      });

      // Should stay in idle state
      expect(result.current.isIdle).toBe(true);
      expect(apiClientModule.apiClient.get).not.toHaveBeenCalled();
    });
  });

  describe("useApplyValuePack mutation", () => {
    it("should apply pack successfully", async () => {
      vi.mocked(apiClientModule.apiClient.post).mockResolvedValueOnce({
        data: { applied: true },
      });

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync("pack-1");

      expect(apiClientModule.apiClient.post).toHaveBeenCalledWith(
        "l3",
        "/packs/pack-1/apply",
        {}
      );
    });

    it("should invalidate cache on success", async () => {
      const queryClient = new QueryClient();
      const invalidateQueriesSpy = vi.spyOn(queryClient, "invalidateQueries");

      vi.mocked(apiClientModule.apiClient.post).mockResolvedValueOnce({
        data: { applied: true },
      });

      const Wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      );

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: Wrapper,
      });

      await result.current.mutateAsync("pack-1");

      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: expect.arrayContaining(["value-packs"]),
      });
    });
  });
});
