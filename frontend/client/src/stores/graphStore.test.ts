import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useGraphStore, type GraphNode, type GraphEdge } from "./graphStore";
import * as apiClientModule from "@/api/client";

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const createMockResponse = <T,>(data: T) => ({
  data,
  status: 200,
  statusText: "OK",
  headers: {},
  config: {} as any,
});

const mockNode: GraphNode = {
  id: "cap-001",
  label: "Real-Time Analytics",
  type: "capability",
  confidence: 0.95,
  x: 100,
  y: 100,
  r: 5,
  properties: { domain: "Analytics" },
};

const mockEdge: GraphEdge = {
  source: "cap-001",
  target: "cap-002",
  type: "requires",
  weight: 0.8,
  properties: {},
};

describe("useGraphStore", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    const { result } = renderHook(() => useGraphStore());
    act(() => {
      result.current.clearError();
      result.current.selectNode(null);
      result.current.setFilters({ minConfidence: 0, nodeTypes: [], edgeTypes: [] });
    });
  });

  describe("initial state", () => {
    it("should have empty graph data initially", () => {
      const { result } = renderHook(() => useGraphStore());

      expect(result.current.graphData.nodes).toEqual([]);
      expect(result.current.graphData.edges).toEqual([]);
    });

    it("should have default filters", () => {
      const { result } = renderHook(() => useGraphStore());

      expect(result.current.filters.minConfidence).toBe(0);
      expect(result.current.filters.nodeTypes).toEqual([]);
      expect(result.current.filters.edgeTypes).toEqual([]);
    });

    it("should not be loading initially", () => {
      const { result } = renderHook(() => useGraphStore());

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("fetchGraph", () => {
    it("should fetch graph data successfully", async () => {
      const mockGraphData = {
        nodes: [mockNode],
        edges: [mockEdge],
        stats: {
          total_nodes: 1,
          total_edges: 1,
          node_types: { capability: 1 },
          communities: 1,
          density: 0.5,
        },
      };

      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse(mockGraphData)
      );

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchGraph();
      });

      expect(result.current.graphData.nodes).toHaveLength(1);
      expect(result.current.graphData.edges).toHaveLength(1);
      expect(result.current.graphData.stats?.total_nodes).toBe(1);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should fetch graph with root entity ID", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse({ nodes: [], edges: [] })
      );

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchGraph("cap-001");
      });

      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("cap-001")
      );
    });

    it("should handle fetch error", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Network error")
      );

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchGraph();
      });

      expect(result.current.error).toBe("Network error");
      expect(result.current.isLoading).toBe(false);
    });

    it("should set loading state during fetch", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockImplementationOnce(
        () => new Promise((resolve) => setTimeout(() => resolve(createMockResponse({ nodes: [], edges: [] })), 100))
      );

      const { result } = renderHook(() => useGraphStore());

      act(() => {
        result.current.fetchGraph();
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => expect(result.current.isLoading).toBe(false));
    });
  });

  describe("fetchSubgraph", () => {
    it("should fetch subgraph with entity ID", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse({ nodes: [mockNode], edges: [] })
      );

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchSubgraph("cap-001");
      });

      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("/entities/cap-001/subgraph")
      );
    });

    it("should fetch subgraph with custom depth", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce(
        createMockResponse({ nodes: [], edges: [] })
      );

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchSubgraph("cap-001", 3);
      });

      expect(apiClientModule.apiClient.get).toHaveBeenCalledWith(
        "l3",
        expect.stringContaining("depth=3")
      );
    });
  });

  describe("node selection", () => {
    it("should select a node", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.selectNode(mockNode));

      expect(result.current.selectedNode).toEqual(mockNode);
    });

    it("should clear node selection", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.selectNode(mockNode));
      act(() => result.current.selectNode(null));

      expect(result.current.selectedNode).toBeNull();
    });

    it("should switch between nodes", () => {
      const { result } = renderHook(() => useGraphStore());

      const node1 = { ...mockNode, id: "cap-001", label: "Node 1" };
      const node2 = { ...mockNode, id: "cap-002", label: "Node 2" };

      act(() => result.current.selectNode(node1));
      expect(result.current.selectedNode?.label).toBe("Node 1");

      act(() => result.current.selectNode(node2));
      expect(result.current.selectedNode?.label).toBe("Node 2");
    });
  });

  describe("filter management", () => {
    it("should set min confidence filter", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.setFilters({ minConfidence: 0.8 }));

      expect(result.current.filters.minConfidence).toBe(0.8);
    });

    it("should set node types filter", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.setFilters({ nodeTypes: ["capability", "usecase"] }));

      expect(result.current.filters.nodeTypes).toEqual(["capability", "usecase"]);
    });

    it("should set edge types filter", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.setFilters({ edgeTypes: ["requires", "enables"] }));

      expect(result.current.filters.edgeTypes).toEqual(["requires", "enables"]);
    });

    it("should merge partial filter updates", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.setFilters({ minConfidence: 0.5 }));
      act(() => result.current.setFilters({ nodeTypes: ["capability"] }));

      expect(result.current.filters.minConfidence).toBe(0.5);
      expect(result.current.filters.nodeTypes).toEqual(["capability"]);
    });

    it("should handle empty filter arrays", () => {
      const { result } = renderHook(() => useGraphStore());

      act(() => result.current.setFilters({ nodeTypes: [], edgeTypes: [] }));

      expect(result.current.filters.nodeTypes).toEqual([]);
      expect(result.current.filters.edgeTypes).toEqual([]);
    });
  });

  describe("error handling", () => {
    it("should clear error", async () => {
      vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
        new Error("Test error")
      );

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchGraph();
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

      const { result } = renderHook(() => useGraphStore());

      await act(async () => {
        await result.current.fetchGraph();
      });

      expect(result.current.error).toBe("Detailed error message");
    });
  });
});
