import { create } from 'zustand';
import { apiClient } from '@/api/client';

export interface TruthStatement {
  id: string;
  statement: string;
  confidence: number;
  evidence: string[];
  contradictions: string[];
  sources: string[];
  createdAt: string;
}

interface TruthState {
  truths: TruthStatement[];
  selectedTruth: TruthStatement | null;
  contradictions: Array<{ id: string; statements: string[]; severity: 'high' | 'medium' | 'low' }>;
  isLoading: boolean;
  error: string | null;

  fetchTruths: () => Promise<void>;
  fetchTruthById: (id: string) => Promise<void>;
  validateStatement: (statement: string) => Promise<TruthStatement>;
  submitCorrection: (truthId: string, correction: string) => Promise<void>;
  selectTruth: (truth: TruthStatement | null) => void;
  fetchContradictions: () => Promise<void>;
  clearError: () => void;
}

export const useTruthStore = create<TruthState>((set) => ({
  truths: [],
  selectedTruth: null,
  contradictions: [],
  isLoading: false,
  error: null,

  fetchTruths: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('l5', '/truths');
      set({ truths: response.data.truths || [], isLoading: false });
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as Error).message;
      set({ error: message, isLoading: false });
    }
  },

  fetchTruthById: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('l5', `/truths/${id}`);
      set({ selectedTruth: response.data, isLoading: false });
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as Error).message;
      set({ error: message, isLoading: false });
    }
  },

  validateStatement: async (statement) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('l5', '/truths/validate', {
        statement,
      });
      set({ isLoading: false });
      return response.data;
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as Error).message;
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  submitCorrection: async (truthId, correction) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post('l5', `/truths/${truthId}/corrections`, {
        correction,
      });
      set({ isLoading: false });
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as Error).message;
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  selectTruth: (truth) => set({ selectedTruth: truth }),

  fetchContradictions: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('l5', '/contradictions');
      set({ contradictions: response.data.contradictions || [], isLoading: false });
    } catch (err) {
      const message = (err as any).response?.data?.detail || (err as Error).message;
      set({ error: message, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
