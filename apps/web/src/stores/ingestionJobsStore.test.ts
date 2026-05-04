import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useIngestionJobsStore } from './ingestionJobsStore';

describe('useIngestionJobsStore', () => {
  beforeEach(() => {
    const { result } = renderHook(() => useIngestionJobsStore());
    act(() => result.current.reset());
  });

  describe('initial state', () => {
    it('has null selectedJobId', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      expect(result.current.selectedJobId).toBeNull();
    });

    it('has default filters', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      expect(result.current.filters).toEqual({
        status: 'all',
        source: '',
        dateFrom: '',
        dateTo: '',
      });
    });
  });

  describe('setSelectedJobId', () => {
    it('sets the selected job ID', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setSelectedJobId('job-42'));
      expect(result.current.selectedJobId).toBe('job-42');
    });

    it('can be set to null', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setSelectedJobId('job-1'));
      act(() => result.current.setSelectedJobId(null));
      expect(result.current.selectedJobId).toBeNull();
    });
  });

  describe('setStatusFilter', () => {
    it('updates filter status', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setStatusFilter('completed'));
      expect(result.current.filters.status).toBe('completed');
    });

    it('accepts all valid status values', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      const statuses = ['all', 'pending', 'processing', 'completed', 'failed'] as const;
      for (const status of statuses) {
        act(() => result.current.setStatusFilter(status));
        expect(result.current.filters.status).toBe(status);
      }
    });

    it('does not affect other filter fields', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setSourceFilter('sfdc'));
      act(() => result.current.setStatusFilter('failed'));
      expect(result.current.filters.source).toBe('sfdc');
    });
  });

  describe('setSourceFilter', () => {
    it('updates filter source', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setSourceFilter('salesforce'));
      expect(result.current.filters.source).toBe('salesforce');
    });

    it('does not affect other filter fields', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setStatusFilter('pending'));
      act(() => result.current.setSourceFilter('hubspot'));
      expect(result.current.filters.status).toBe('pending');
    });
  });

  describe('setDateFrom / setDateTo', () => {
    it('updates dateFrom filter', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setDateFrom('2024-01-01'));
      expect(result.current.filters.dateFrom).toBe('2024-01-01');
    });

    it('updates dateTo filter', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setDateTo('2024-12-31'));
      expect(result.current.filters.dateTo).toBe('2024-12-31');
    });

    it('both date filters can be set independently', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => {
        result.current.setDateFrom('2024-01-01');
        result.current.setDateTo('2024-06-30');
      });
      expect(result.current.filters.dateFrom).toBe('2024-01-01');
      expect(result.current.filters.dateTo).toBe('2024-06-30');
    });
  });

  describe('resetFilters', () => {
    it('resets all filter fields to defaults', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => {
        result.current.setStatusFilter('failed');
        result.current.setSourceFilter('sfdc');
        result.current.setDateFrom('2024-01-01');
        result.current.setDateTo('2024-12-31');
      });
      act(() => result.current.resetFilters());
      expect(result.current.filters).toEqual({
        status: 'all',
        source: '',
        dateFrom: '',
        dateTo: '',
      });
    });

    it('does not reset selectedJobId', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => result.current.setSelectedJobId('job-99'));
      act(() => result.current.resetFilters());
      expect(result.current.selectedJobId).toBe('job-99');
    });
  });

  describe('reset', () => {
    it('resets all state including selectedJobId and filters', () => {
      const { result } = renderHook(() => useIngestionJobsStore());
      act(() => {
        result.current.setSelectedJobId('job-1');
        result.current.setStatusFilter('processing');
        result.current.setSourceFilter('crm');
      });
      act(() => result.current.reset());
      expect(result.current.selectedJobId).toBeNull();
      expect(result.current.filters).toEqual({
        status: 'all',
        source: '',
        dateFrom: '',
        dateTo: '',
      });
    });
  });
});
