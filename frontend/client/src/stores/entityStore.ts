import { create } from 'zustand';

export interface Entity {
  id: string;
  name: string;
  type: 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver' | 'KPI';
  confidence: number;
  description?: string;
  properties?: Record<string, unknown>;
  createdAt?: string;
}

/**
 * Entity UI State Store
 * ONLY client/UI state - no server state (use React Query for that)
 */
interface EntityUIState {
  selectedEntity: Entity | null;
  searchQuery: string;
  selectedType: string | null;

  selectEntity: (entity: Entity | null) => void;
  setSearchQuery: (query: string) => void;
  setSelectedType: (type: string | null) => void;
  clearFilters: () => void;
}

export const useEntityUIStore = create<EntityUIState>((set) => ({
  selectedEntity: null,
  searchQuery: '',
  selectedType: null,

  selectEntity: (entity) => set({ selectedEntity: entity }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedType: (type) => set({ selectedType: type }),
  clearFilters: () => set({ searchQuery: '', selectedType: null }),
}));

