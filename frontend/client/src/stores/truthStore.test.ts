import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useTruthStore, type TruthStatement } from "./truthStore";
import * as apiClientModule from "@/api/client";

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const createMockResponse = <T,>(data: T) => ({
  data,
  status: 200,
  statusText: "OK",
  headers: {},
  config: {} as any,
});

const mockTruth: TruthStatement = {
  id: "truth-001",
  statement: "Real-time analytics improves decision speed by 40%",
  confidence: 0.92,
  evidence: ["Study A", "Case Study B"],
  contradictions: [],
  sources: ["Research Paper 1"],
  createdAt: "2024-01-01T00:00:00Z",
};

describe("useTruthStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    const { result } = renderHook(() => useTruthStore());
    act(() => {
      result.current.clearError();
      result.current.selectTruth(null);
    });
  });

  describe("initial state", () => {
    it("should have empty truths array initially", () => {
      const { result } = renderHook(() => useTruthStore());

      expect(result.current.truths).toEqual([]);
    });

    it("should have no selected truth initially", () => {
      const { result } = renderHook(() => useTruthStore());

      expect(result.current.selectedTruth).toBeNull();
    });

    it("should have empty contradictions initially", () => {
      const { result } = renderHook(() => useTruthStore());

      expect(result.current.contradictions).toEqual([]);
    });

    it("should not be loading initially", () => {
      const { result } = renderHook(() => useTruthStore());

      expect(result.current.isLoading).toBe(false);
    });

    it("should have no error initially", () => {
      const { result } = renderHook(() => useTruthStore());

      expect(result.current.error).toBeNull();
    });
  });

  describe("fetchTruths", () => {
    it("should fetch truths successfully", async () => {
      const mockTruths = {
        truths: [mockTruth, { ...mockTruth, id: "truth-002" }],
      };

      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse(mockTruths)
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruths();
      });

      expect(result.current.truths).toHaveLength(2);
      expect(result.current.truths[0].statement).toBe(mockTruth.statement);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should handle empty truths response", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse({ truths: [] })
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruths();
      });

      expect(result.current.truths).toEqual([]);
    });

    it("should handle fetch error", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Network error")
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruths();
      });

      expect(result.current.error).toBe("Network error");
      expect(result.current.isLoading).toBe(false);
    });

    it("should set loading state during fetch", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockImplementationOnce(
        () => new Promise((resolve) => setTimeout(() => resolve(createMockResponse({ truths: [] })), 100))
      );

      const { result } = renderHook(() => useTruthStore());

      act(() => {
        result.current.fetchTruths();
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => expect(result.current.isLoading).toBe(false));
    });
  });

  describe("fetchTruthById", () => {
    it("should fetch single truth by ID", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse(mockTruth)
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruthById("truth-001");
      });

      expect(result.current.selectedTruth).toEqual(mockTruth);
      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l5",
        "/truths/truth-001"
      );
    });

    it("should handle fetch truth error", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Truth not found")
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruthById("invalid-id");
      });

      expect(result.current.error).toBe("Truth not found");
      expect(result.current.selectedTruth).toBeNull();
    });
  });

  describe("validateStatement", () => {
    it("should validate statement and return truth", async () => {
      vi.mocked(apiClientModule.apiClient.post).mockResolvedValueOnce(
        createMockResponse(mockTruth)
      );

      const { result } = renderHook(() => useTruthStore());

      let validationResult: TruthStatement | undefined;
      await act(async () => {
        validationResult = await result.current.validateStatement(
          "Real-time analytics improves decision speed"
        );
      });

      expect(validationResult).toEqual(mockTruth);
      expect(apiClientModule.apiClient.post).toHaveBeenCalledWith(
        "l5",
        "/truths/validate",
        { statement: "Real-time analytics improves decision speed" }
      );
    });

    it("should handle validation error", async () => {
      vi.mocked(apiClientModule.apiClient.post).mockRejectedValueOnce(
        new Error("Validation failed")
      );

      const { result } = renderHook(() => useTruthStore());

      // Catch the error and verify state separately
      try {
        await act(async () => {
          await result.current.validateStatement("Invalid statement");
        });
      } catch (e) {
        // Expected to throw
      }

      expect(result.current.error).toBe("Validation failed");
    });

    it("should set loading during validation", async () => {
      vi.mocked(apiClientModule.apiClient.post).mockImplementationOnce(
        () => new Promise((resolve) => setTimeout(() => resolve(createMockResponse(mockTruth)), 100))
      );

      const { result } = renderHook(() => useTruthStore());

      act(() => {
        result.current.validateStatement("Test");
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => expect(result.current.isLoading).toBe(false));
    });
  });

  describe("submitCorrection", () => {
    it("should submit correction successfully", async () => {
      vi.mocked(apiClientModule.apiClient.post).mockResolvedValueOnce(
        createMockResponse({ success: true })
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.submitCorrection("truth-001", "Updated statement");
      });

      expect(apiClientModule.apiClient.post).toHaveBeenCalledWith(
        "l5",
        "/truths/truth-001/corrections",
        { correction: "Updated statement" }
      );
    });

    it("should handle correction submission error", async () => {
      vi.mocked(apiClientModule.apiClient.post).mockRejectedValueOnce(
        new Error("Failed to submit")
      );

      const { result } = renderHook(() => useTruthStore());

      try {
        await act(async () => {
          await result.current.submitCorrection("truth-001", "Correction");
        });
      } catch (e) {
        // Expected to throw
      }

      expect(result.current.error).toBe("Failed to submit");
    });
  });

  describe("selectTruth", () => {
    it("should select a truth", () => {
      const { result } = renderHook(() => useTruthStore());

      act(() => result.current.selectTruth(mockTruth));

      expect(result.current.selectedTruth).toEqual(mockTruth);
    });

    it("should clear truth selection", () => {
      const { result } = renderHook(() => useTruthStore());

      act(() => result.current.selectTruth(mockTruth));
      act(() => result.current.selectTruth(null));

      expect(result.current.selectedTruth).toBeNull();
    });
  });

  describe("fetchContradictions", () => {
    it("should fetch contradictions successfully", async () => {
      const mockContradictions = {
        contradictions: [
          { id: "contr-001", statements: ["truth-001", "truth-002"], severity: "high" },
        ],
      };

      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse(mockContradictions)
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchContradictions();
      });

      expect(result.current.contradictions).toHaveLength(1);
      expect(result.current.contradictions[0].severity).toBe("high");
    });

    it("should handle empty contradictions", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse({ contradictions: [] })
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchContradictions();
      });

      expect(result.current.contradictions).toEqual([]);
    });

    it("should handle fetch contradictions error", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Failed to fetch")
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchContradictions();
      });

      expect(result.current.error).toBe("Failed to fetch");
    });
  });

  describe("error handling", () => {
    it("should clear error", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Test error")
      );

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruths();
      });

      expect(result.current.error).toBe("Test error");

      act(() => result.current.clearError());

      expect(result.current.error).toBeNull();
    });

    it("should handle API error with response detail", async () => {
      const error = {
        response: { data: { detail: "Detailed error message" } },
        message: "Request failed",
      };
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useTruthStore());

      await act(async () => {
        await result.current.fetchTruths();
      });

      expect(result.current.error).toBe("Detailed error message");
    });
  });
});
