import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper, createWrapperWithRetry, createMockResponse } from "../test-utils";
import {
  useModels,
  useModelFolders,
  useCreateModel,
  useDeleteModel,
  ModelApiError,
  type ModelFilters,
  type CreateModelPayload,
} from "./useModels";
import { apiClient } from "@/api/client";

// Mock the API client
vi.mock("@/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/client")>();
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
    },
  };
});

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe("useModels", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("useModels hook", () => {
    it("should fetch models successfully", async () => {
      const mockBackendResponse = {
        models: [
          {
            model_id: "mdl_001",
            name: "SaaS Revenue Optimization",
            description: "End-to-end value model",
            industry: "SaaS / B2B",
            tags: ["revenue", "churn"],
            status: "active",
            folder: "my-models",
            formula_count: 14,
            entity_count: 32,
            driver_count: 8,
            created_at: "2026-03-15T10:00:00Z",
            updated_at: "2026-04-16T14:30:00Z",
            owner: "user-001",
            is_shared: false,
          },
        ],
        total: 1,
        offset: 0,
        limit: 50,
        filters_applied: {},
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockBackendResponse));

      const { result } = renderHook(() => useModels(), {
        wrapper: createWrapper(),
      });

      // Should start loading
      expect(result.current.isLoading).toBe(true);

      // Wait for success
      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Verify transformed data
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0]).toMatchObject({
        id: "mdl_001",
        name: "SaaS Revenue Optimization",
        formulaCount: 14,
        entityCount: 32,
        isShared: false,
      });
    });

    it("should apply filters to API request", async () => {
      const mockResponse = {
        models: [],
        total: 0,
        offset: 0,
        limit: 50,
        filters_applied: {
          search: "revenue",
          folder: "my-models",
          industry: "SaaS / B2B",
          status: "active",
          sort_by: "updated_at",
          sort_dir: "desc",
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockResponse));

      const filters: ModelFilters = {
        search: "revenue",
        folder: "my-models",
        industry: "SaaS / B2B",
        status: "active",
        sortBy: "updatedAt",
        sortDir: "desc",
      };

      renderHook(() => useModels(filters), { wrapper: createWrapper() });

      await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

      // Verify correct endpoint with query params
      const callArg = vi.mocked(apiClient.get).mock.calls[0][1];
      expect(callArg).toContain("/models?");
      expect(callArg).toContain("search=revenue");
      expect(callArg).toContain("folder=my-models");
      // URLSearchParams encodes spaces as + and / as %2F
      expect(callArg).toContain("industry=SaaS");
      expect(callArg).toContain("B2B");
      expect(callArg).toContain("status=active");
      expect(callArg).toContain("sort_by=updated_at");
      expect(callArg).toContain("sort_dir=desc");
    });

    it("should handle API error state", async () => {
      const { toast } = await import("sonner");
      
      vi.mocked(apiClient.get).mockRejectedValueOnce(
        new Error("Failed to fetch models")
      );

      const { result } = renderHook(() => useModels(), {
        wrapper: createWrapperWithRetry(false),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(ModelApiError);
      expect(result.current.error?.message).toContain("Failed to fetch models");
    });

    it("should not include 'all' folder in API params", async () => {
      const mockResponse = {
        models: [],
        total: 0,
        offset: 0,
        limit: 50,
        filters_applied: {},
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockResponse));

      renderHook(() => useModels({ folder: "all" }), { wrapper: createWrapper() });

      await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

      const callArg = vi.mocked(apiClient.get).mock.calls[0][1];
      expect(callArg).not.toContain("folder=all");
    });
  });

  describe("useModelFolders hook", () => {
    it("should fetch folder counts", async () => {
      const mockResponse = {
        folders: [
          { folder_id: "all", name: "All Models", count: 10 },
          { folder_id: "my-models", name: "My Models", count: 6 },
          { folder_id: "shared", name: "Shared With Me", count: 3 },
          { folder_id: "favorites", name: "Favorites", count: 1 },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockResponse));

      const { result } = renderHook(() => useModelFolders(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toHaveLength(4);
      expect(result.current.data?.[0]).toEqual({
        id: "all",
        name: "All Models",
        count: 10,
      });
    });

    it("should call correct endpoint", async () => {
      const mockResponse = { folders: [] };
      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockResponse));

      renderHook(() => useModelFolders(), { wrapper: createWrapper() });

      await waitFor(() => expect(apiClient.get).toHaveBeenCalledWith("l3", "/models/folders"));
    });
  });

  describe("useCreateModel hook", () => {
    it("should create model successfully", async () => {
      const { toast } = await import("sonner");
      const queryClient = { invalidateQueries: vi.fn() };

      const mockResponse = {
        model_id: "mdl_20240101_001",
        message: "Model created successfully",
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(createMockResponse(mockResponse));

      const { result } = renderHook(() => useCreateModel(), {
        wrapper: createWrapper(),
      });

      const payload: CreateModelPayload = {
        name: "New Test Model",
        description: "A test model description",
        industry: "SaaS / B2B",
        tags: ["test", "demo"],
      };

      result.current.mutate(payload);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.post).toHaveBeenCalledWith("l3", "/models", {
        name: "New Test Model",
        description: "A test model description",
        industry: "SaaS / B2B",
        tags: ["test", "demo"],
      });

      expect(result.current.data?.modelId).toBe("mdl_20240101_001");
    });

    it("should trim name and description", async () => {
      const mockResponse = {
        model_id: "mdl_001",
        message: "Model created successfully",
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(createMockResponse(mockResponse));

      const { result } = renderHook(() => useCreateModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        name: "  Padded Name  ",
        description: "  Padded Description  ",
        industry: "SaaS",
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.post).toHaveBeenCalledWith(
        "l3",
        "/models",
        expect.objectContaining({
          name: "Padded Name",
          description: "Padded Description",
        })
      );
    });

    it("should reject empty name", async () => {
      const { result } = renderHook(() => useCreateModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        name: "   ",
        description: "",
        industry: "SaaS",
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(ModelApiError);
      expect(result.current.error?.message).toBe("Model name is required");
    });

    it("should show toast on success", async () => {
      const { toast } = await import("sonner");
      const mockResponse = {
        model_id: "mdl_001",
        message: "Model created successfully",
      };

      vi.mocked(apiClient.post).mockResolvedValueOnce(createMockResponse(mockResponse));

      const { result } = renderHook(() => useCreateModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        name: "Test Model",
        description: "",
        industry: "SaaS",
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(toast.success).toHaveBeenCalledWith(
        "Model created successfully",
        expect.objectContaining({
          description: expect.stringContaining("mdl_001"),
        })
      );
    });

    it("should show toast on error", async () => {
      const { toast } = await import("sonner");

      vi.mocked(apiClient.post).mockRejectedValueOnce(
        new Error("Server error")
      );

      const { result } = renderHook(() => useCreateModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        name: "Test Model",
        description: "",
        industry: "SaaS",
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(toast.error).toHaveBeenCalledWith(
        "Failed to create model",
        expect.objectContaining({
          description: expect.any(String),
        })
      );
    });
  });

  describe("useDeleteModel hook", () => {
    it("should delete model successfully", async () => {
      const { toast } = await import("sonner");

      vi.mocked(apiClient.delete).mockResolvedValueOnce(createMockResponse({}));

      const { result } = renderHook(() => useDeleteModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate("mdl_001");

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.delete).toHaveBeenCalledWith("l3", "/models/mdl_001");
      expect(result.current.data?.modelId).toBe("mdl_001");
    });

    it("should reject empty model ID", async () => {
      const { result } = renderHook(() => useDeleteModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate("");

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeInstanceOf(ModelApiError);
      expect(result.current.error?.message).toBe("Model ID is required");
    });

    it("should show toast on success", async () => {
      const { toast } = await import("sonner");

      vi.mocked(apiClient.delete).mockResolvedValueOnce(createMockResponse({}));

      const { result } = renderHook(() => useDeleteModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate("mdl_123");

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(toast.success).toHaveBeenCalledWith(
        "Model deleted",
        expect.objectContaining({
          description: expect.stringContaining("mdl_123"),
        })
      );
    });

    it("should show toast on error", async () => {
      const { toast } = await import("sonner");

      vi.mocked(apiClient.delete).mockRejectedValueOnce(
        new Error("Not authorized")
      );

      const { result } = renderHook(() => useDeleteModel(), {
        wrapper: createWrapper(),
      });

      result.current.mutate("mdl_123");

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(toast.error).toHaveBeenCalledWith(
        "Failed to delete model",
        expect.any(Object)
      );
    });
  });

  describe("snake_case to camelCase transformation", () => {
    it("should correctly transform all fields", async () => {
      const mockBackendResponse = {
        models: [
          {
            model_id: "mdl_test",
            name: "Test",
            description: "Test description",
            industry: "SaaS",
            tags: ["tag1"],
            status: "draft",
            folder: "my-models",
            formula_count: 5,
            entity_count: 10,
            driver_count: 3,
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-02T00:00:00Z",
            owner: "user-001",
            is_shared: true,
          },
        ],
        total: 1,
        offset: 0,
        limit: 50,
        filters_applied: {},
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockBackendResponse));

      const { result } = renderHook(() => useModels(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const model = result.current.data?.[0];
      expect(model).toBeDefined();
      expect(model?.id).toBe("mdl_test");
      expect(model?.formulaCount).toBe(5);
      expect(model?.entityCount).toBe(10);
      expect(model?.driverCount).toBe(3);
      expect(model?.createdAt).toBe("2024-01-01T00:00:00Z");
      expect(model?.updatedAt).toBe("2024-01-02T00:00:00Z");
      expect(model?.isShared).toBe(true);
    });
  });
});
