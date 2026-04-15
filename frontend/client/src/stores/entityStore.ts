/**
 * Entity UI Store — UI state for the Ontology Browser
 *
 * Manages:
 * - Search query for entity filtering
 * - Selected entity type filter
 * - UI state that doesn't need server persistence
 */

import { create } from 'zustand';

export type EntityType = 'capability' | 'usecase' | 'persona' | 'valuedriver';

export interface EntityUIStore {
  /** Search query for filtering entities */
  searchQuery: string;
  setSearchQuery: (value: string) => void;

  /** Selected entity type filter (null = all types) */
  selectedType: EntityType | null;
  setSelectedType: (type: EntityType | null) => void;

  /** Clear all filters */
  clearFilters: () => void;

  /** Reset to defaults */
  reset: () => void;
}

const DEFAULTS = {
  searchQuery: '',
  selectedType: null as EntityType | null,
};

export const useEntityUIStore = create<EntityUIStore>((set) => ({
  ...DEFAULTS,
  setSearchQuery: (value) => set({ searchQuery: value }),
  setSelectedType: (type) => set({ selectedType: type }),
  clearFilters: () => set({ searchQuery: '', selectedType: null }),
  reset: () => set(DEFAULTS),
}));
