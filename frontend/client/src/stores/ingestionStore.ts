import { create } from 'zustand';

/**
 * Ingestion UI State Store
 * ONLY client/UI state - no server state (use React Query for that)
 */
interface IngestionUIState {
  domainInput: string;

  setDomainInput: (value: string) => void;
}

export const useIngestionUIStore = create<IngestionUIState>((set) => ({
  domainInput: '',

  setDomainInput: (value) => set({ domainInput: value }),
}));

