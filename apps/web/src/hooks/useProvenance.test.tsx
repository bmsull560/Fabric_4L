import React from 'react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import {
  useProvenanceTrail,
  useAuditLogs,
  useExportProvenance,
  type ProvenanceTrail,
  type AuditLogEntry,
  type AuditLogResponse,
} from './useProvenance';

// Mock the apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

// Helper to create mock responses
function createMockResponse<T>(data: T): { data: T; status: number } {
  return { data, status: 200 };
}

// Helper to create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

// Sample data
const sampleProvenanceTrail: ProvenanceTrail = {
  entity_id: 'ent-001',
  entity_type: 'UseCase',
  entity_name: 'Pipeline Forecast',
  created_at: '2024-01-01T00:00:00Z',
  source: 'extraction-job-001',
  extraction_job_id: 'job-001',
  confidence_score: 0.95,
  steps: [
    {
      step: 1,
      label: 'Entity Created',
      detail: 'Entity ent-001 created from source document',
      timestamp: '2024-01-01T00:00:00Z',
      agent: 'ExtractionEngine-v2.1',
    },
    {
      step: 2,
      label: 'Value Calculated',
      detail: 'ROI calculated from benchmarks',
      timestamp: '2024-01-01T01:00:00Z',
      agent: 'ValueCalculator',
      entity_id: 'val-001',
    },
  ],
};

const sampleAuditLogEntry: AuditLogEntry = {
  id: 'audit-001',
  timestamp: '2024-01-01T00:00:00Z',
  source: 'provenance',
  event_type: 'entity_created',
  entity_id: 'ent-001',
  entity_type: 'UseCase',
  action: 'create',
  agent: 'ExtractionEngine',
  details: { confidence: 0.95 },
};

const sampleAuditLogResponse: AuditLogResponse = {
  entries: [sampleAuditLogEntry],
  total: 1,
  page: 1,
  per_page: 50,
};

describe('useProvenance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useProvenanceTrail hook', () => {
    it('should fetch provenance trail successfully', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse(sampleProvenanceTrail)
      );

      const { result } = renderHook(() => useProvenanceTrail('ent-001'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith('l3', '/provenance/ent-001');
      expect(result.current.data?.entity_id).toBe('ent-001');
      expect(result.current.data?.steps).toHaveLength(2);
    });

    it('should not fetch when entityId is null', () => {
      renderHook(() => useProvenanceTrail(null), {
        wrapper: createWrapper(),
      });

      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('should handle API error', async () => {
      (apiClient.get as Mock).mockRejectedValueOnce(new Error('Not found'));

      const { result } = renderHook(() => useProvenanceTrail('ent-999'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
    });

    it('should encode entity ID in URL', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse(sampleProvenanceTrail)
      );

      renderHook(() => useProvenanceTrail('ent with spaces'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

      const callUrl = (apiClient.get as Mock).mock.calls[0][1];
      expect(callUrl).toContain('ent%20with%20spaces');
    });
  });

  describe('useAuditLogs hook', () => {
    it('should fetch audit logs successfully', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse(sampleAuditLogResponse)
      );

      const { result } = renderHook(() => useAuditLogs(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith('l3', '/audit/logs?');
      expect(result.current.data?.entries).toHaveLength(1);
      expect(result.current.data?.total).toBe(1);
    });

    it('should apply filters correctly', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse(sampleAuditLogResponse)
      );

      renderHook(
        () =>
          useAuditLogs({
            source: 'provenance',
            from_date: '2024-01-01T00:00:00Z',
            to_date: '2024-01-02T00:00:00Z',
            entity_type: 'UseCase',
            event_type: 'entity_created',
            agent: 'ExtractionEngine',
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

      const callUrl = (apiClient.get as Mock).mock.calls[0][1];
      expect(callUrl).toContain('source=provenance');
      expect(callUrl).toContain('from_date=');
      expect(callUrl).toContain('to_date=');
      expect(callUrl).toContain('entity_type=UseCase');
      expect(callUrl).toContain('event_type=entity_created');
      expect(callUrl).toContain('agent=ExtractionEngine');
    });

    it('should handle empty response', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse({ entries: [], total: 0, page: 1, per_page: 50 })
      );

      const { result } = renderHook(() => useAuditLogs(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.entries).toHaveLength(0);
      expect(result.current.data?.total).toBe(0);
    });
  });

  describe('useExportProvenance mutation', () => {
    it('should export provenance in JSON format', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse(sampleProvenanceTrail)
      );

      const { result } = renderHook(() => useExportProvenance(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ entityId: 'ent-001', format: 'json' });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith(
        'l3',
        '/provenance/ent-001?format=json'
      );
    });

    it('should export provenance in PROV-O format', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse({
          ...sampleProvenanceTrail,
          prov_o_rdf: '<rdf>...</rdf>',
        })
      );

      const { result } = renderHook(() => useExportProvenance(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ entityId: 'ent-001', format: 'prov-o' });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith(
        'l3',
        '/provenance/ent-001?format=prov-o'
      );
    });

    it('should handle export error', async () => {
      (apiClient.get as Mock).mockRejectedValueOnce(new Error('Export failed'));

      const { result } = renderHook(() => useExportProvenance(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ entityId: 'ent-001' });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });
});
