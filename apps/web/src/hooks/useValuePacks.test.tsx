import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper, createWrapperWithRetry, createMockResponse } from "../test-utils";
import { useValuePacks, useValuePack, useApplyValuePack, ValuePackApiError } from "./useValuePacks";
import { apiClient } from "@/api/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { QK } from "./queryKeys";

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
          id: "pack-1",
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

      // P1 Fix: Use createWrapperWithRetry(false) to disable retries for faster error state testing
      // This reduces test time from ~15s (with retries) to ~1s
      const { result } = renderHook(() => useValuePacks(), {
        wrapper: createWrapperWithRetry(false),
      });

      // Wait for error state without retries
      await waitFor(
        () => expect(result.current.isError).toBe(true),
        { timeout: 5000 }
      );

      expect(result.current.error).toBeDefined();
      expect(result.current.error?.message).toBe("Network error");
    }, 10000);

    it("should reject malformed pack list responses", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(
        createMockResponse([{ pack_id: "pack-1", name: "Missing required fields" }])
      );

      const { result } = renderHook(() => useValuePacks(), {
        wrapper: createWrapperWithRetry(false),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(ValuePackApiError);
    });
  });

  describe("useValuePack hook (single pack)", () => {
    it("should fetch single pack by ID", async () => {
      const mockPack = {
        id: "pack-1",
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
      vi.mocked(apiClient.post).mockResolvedValueOnce(
        createMockResponse({ success: true, message: "Applied" })
      );

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: createWrapper(),
      });

      await expect(result.current.mutateAsync({ packId: "pack-1" })).resolves.toEqual({
        success: true,
        message: "Applied",
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        "l3",
        "/packs/pack-1/apply",
        {}
      );
    });

    it("cancels queries with correct cache keys during optimistic update", async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const cancelSpy = vi.spyOn(queryClient, "cancelQueries");

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      vi.mocked(apiClient.post).mockResolvedValueOnce(
        createMockResponse({ success: true, message: "Applied" })
      );

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: Wrapper,
      });

      result.current.mutate({ packId: "pack-1" });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Verify cancelQueries was called with both detail and list cache keys
      expect(cancelSpy).toHaveBeenCalledWith({ queryKey: QK.valuePacks.detail("pack-1") });
      expect(cancelSpy).toHaveBeenCalledWith({ queryKey: QK.valuePacks.list({}) });
    });

    it("rolls back optimistic update on error", async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      // Pre-populate cache with existing pack
      const initialPack = {
        id: "pack-1",
        pack_id: "pack-1",
        name: "Test Pack",
        industry: "SaaS / B2B",
        status: "draft" as const,
        scope: "global" as const,
        driver_count: 5,
        formula_count: 10,
        benchmark_count: 5,
        workflow_count: 2,
        updated_at: "2024-01-01T00:00:00Z",
      };
      queryClient.setQueryData(QK.valuePacks.detail("pack-1"), initialPack);
      queryClient.setQueryData(QK.valuePacks.list({}), [initialPack]);

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new ValuePackApiError("Pack not found", 404)
      );

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: Wrapper,
      });

      await expect(result.current.mutateAsync({ packId: "pack-1" })).rejects.toThrow();

      await waitFor(() => expect(result.current.isError).toBe(true));

      // Verify cache was rolled back to initial state
      const finalDetail = queryClient.getQueryData(QK.valuePacks.detail("pack-1"));
      const finalList = queryClient.getQueryData(QK.valuePacks.list({}));
      expect(finalDetail).toEqual(initialPack);
      expect(finalList).toEqual([initialPack]);
    });

    it("optimistically updates pack status to active", async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      // Pre-populate cache with draft pack
      const draftPack = {
        id: "pack-1",
        pack_id: "pack-1",
        name: "Test Pack",
        industry: "SaaS / B2B",
        status: "draft" as const,
        scope: "global" as const,
        driver_count: 5,
        formula_count: 10,
        benchmark_count: 5,
        workflow_count: 2,
        updated_at: "2024-01-01T00:00:00Z",
      };
      queryClient.setQueryData(QK.valuePacks.detail("pack-1"), draftPack);
      queryClient.setQueryData(QK.valuePacks.list({}), [draftPack]);

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      vi.mocked(apiClient.post).mockImplementation(() =>
        new Promise((resolve) => setTimeout(() => resolve(createMockResponse({ success: true })), 100))
      );

      const { result } = renderHook(() => useApplyValuePack(), {
        wrapper: Wrapper,
      });

      result.current.mutate({ packId: "pack-1" });

      // Check optimistic update immediately after mutation starts
      await waitFor(() => {
        const optimisticDetail = queryClient.getQueryData(QK.valuePacks.detail("pack-1"));
        const optimisticList = queryClient.getQueryData(QK.valuePacks.list({}));
        expect(optimisticDetail?.status).toBe("active");
        expect(optimisticList?.[0]?.status).toBe("active");
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });
});
