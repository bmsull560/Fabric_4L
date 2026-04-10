import { create } from 'zustand';
import { apiClient } from '@/api/client';

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  confidence: number;
  x?: number;
  y?: number;
  r?: number;
  properties?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
  properties?: Record<string, unknown>;
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  node_types: Record<string, number>;
  communities: number;
  density: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats?: GraphStats;
}

interface GraphState {
  graphData: GraphData;
  selectedNode: GraphNode | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    minConfidence: number;
    nodeTypes: string[];
    edgeTypes: string[];
  };

  fetchGraph: (rootEntityId?: string) => Promise<void>;
  fetchSubgraph: (entityId: string, depth?: number) => Promise<void>;
  selectNode: (node: GraphNode | null) => void;
  setFilters: (filters: Partial<GraphState['filters']>) => void;
  clearError: () => void;
}

export const useGraphStore = create<GraphState>((set, get) => ({
  graphData: { nodes: [], edges: [] },
  selectedNode: null,
  isLoading: false,
  error: null,
  filters: {
    minConfidence: 0.7,
    nodeTypes: [],
    edgeTypes: [],
  },

  fetchGraph: async (rootEntityId) => {
    set({ isLoading: true, error: null });
    try {
      const url = rootEntityId ? `/graph?root=${rootEntityId}` : '/graph';
      const response = await apiClient.get('l3', url);
      const data = response.data;
      set({
        graphData: {
          nodes: data.nodes || [],
          edges: data.edges || [],
          stats: data.stats,
        },
        isLoading: false
      });
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as any).response?.data?.message || (err as Error).message;
      set({ error: message, isLoading: false });
    }
  },

  fetchSubgraph: async (entityId, depth = 2) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get(
        'l3',
        `/entities/${entityId}/subgraph?depth=${depth}`
      );
      const data = response.data;
      set({
        graphData: {
          nodes: data.nodes || [],
          edges: data.edges || [],
          stats: data.stats,
        },
        isLoading: false
      });
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as any).response?.data?.message || (err as Error).message;
      set({ error: message, isLoading: false });
    }
  },

  selectNode: (node) => set({ selectedNode: node }),

  setFilters: (newFilters) => {
    set((state) => ({ filters: { ...state.filters, ...newFilters } }));
  },

  clearError: () => set({ error: null }),
}));
