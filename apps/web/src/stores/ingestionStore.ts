/**
 * Ingestion UI Store — UI state for the Command Center
 *
 * Manages:
 * - Domain input text for ingestion
 * - UI state that doesn't need server persistence
 */

import { create } from 'zustand';

export interface IngestionUIStore {
  /** Domain URL input for ingestion */
  domainInput: string;
  setDomainInput: (value: string) => void;

  /** Reset to default */
  reset: () => void;
}

const DEFAULTS = {
  domainInput: '',
};

export const useIngestionUIStore = create<IngestionUIStore>((set) => ({
  ...DEFAULTS,
  setDomainInput: (value) => set({ domainInput: value }),
  reset: () => set(DEFAULTS),
}));
