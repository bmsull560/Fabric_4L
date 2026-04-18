/**
 * Ingestion Jobs UI Store — Page-local UI state for the Ingestion Jobs page
 *
 * Manages:
 * - Selected job ID for detail/logs panels
 * - Filter state (status, date range, source)
 * - Reset functionality
 */

import { create } from 'zustand';

export type JobStatusFilter = 'all' | 'pending' | 'processing' | 'completed' | 'failed';

export interface JobFilters {
  status: JobStatusFilter;
  source: string;
  dateFrom: string;
  dateTo: string;
}

export interface IngestionJobsUIStore {
  /** Currently selected job ID for detail/logs panels */
  selectedJobId: string | null;
  setSelectedJobId: (id: string | null) => void;

  /** Filter state */
  filters: JobFilters;
  setStatusFilter: (status: JobStatusFilter) => void;
  setSourceFilter: (source: string) => void;
  setDateFrom: (date: string) => void;
  setDateTo: (date: string) => void;
  resetFilters: () => void;

  /** Reset all to defaults */
  reset: () => void;
}

const DEFAULT_FILTERS: JobFilters = {
  status: 'all',
  source: '',
  dateFrom: '',
  dateTo: '',
};

const DEFAULTS = {
  selectedJobId: null as string | null,
  filters: DEFAULT_FILTERS,
};

export const useIngestionJobsStore = create<IngestionJobsUIStore>((set) => ({
  ...DEFAULTS,

  setSelectedJobId: (id) => set({ selectedJobId: id }),

  setStatusFilter: (status) =>
    set((state) => ({ filters: { ...state.filters, status } })),

  setSourceFilter: (source) =>
    set((state) => ({ filters: { ...state.filters, source } })),

  setDateFrom: (dateFrom) =>
    set((state) => ({ filters: { ...state.filters, dateFrom } })),

  setDateTo: (dateTo) =>
    set((state) => ({ filters: { ...state.filters, dateTo } })),

  resetFilters: () =>
    set((state) => ({ filters: DEFAULT_FILTERS })),

  reset: () => set(DEFAULTS),
}));
