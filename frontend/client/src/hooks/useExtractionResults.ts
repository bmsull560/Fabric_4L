/**
 * useExtractionResults.ts - Query hook for extraction job results
 * 
 * Fetches completed extraction results (entities, relationships) from
 * the Layer 2 API for display in the results table.
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from '@/hooks/queryKeys';
import { STALE_TIME } from '@/hooks/useApiShared';

export interface ExtractionResult {
  /** Job ID */
  jobId: string;
  /** Overall status */
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  /** Extraction phase status */
  extractionStatus: string;
  /** Number of entities extracted */
  entitiesExtracted: number;
  /** Number of relationships extracted */
  relationshipsExtracted: number;
  /** Error message if failed */
  lastError: string | null;
  /** Start time */
  startedAt: string;
  /** Completion time */
  completedAt: string | null;
}

export interface ExtractedEntity {
  /** Entity name */
  name: string;
  /** Entity type (Capability, UseCase, Persona, ValueDriver) */
  type: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** Source document URL */
  source: string;
  /** Extraction status */
  status: 'extracted' | 'pending' | 'failed';
}

interface ApiExtractionStatusResponse {
  job_id: string;
  overall_status: string;
  extraction_status: string;
  ingestion_status?: string;
  entities_extracted: number;
  relationships_extracted: number;
  last_error: string | null;
  started_at: string;
  completed_at: string | null;
}

function mapExtractionResult(apiData: ApiExtractionStatusResponse): ExtractionResult {
  const statusMap: Record<string, ExtractionResult['status']> = {
    'PENDING': 'pending',
    'QUEUED': 'pending',
    'RUNNING': 'running',
    'EXTRACTING': 'running',
    'TRANSFORMING': 'running',
    'STORING': 'running',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'cancelled',
  };

  return {
    jobId: apiData.job_id,
    status: statusMap[apiData.overall_status] || 'pending',
    extractionStatus: apiData.extraction_status,
    entitiesExtracted: apiData.entities_extracted ?? 0,
    relationshipsExtracted: apiData.relationships_extracted ?? 0,
    lastError: apiData.last_error,
    startedAt: apiData.started_at,
    completedAt: apiData.completed_at,
  };
}

/**
 * Get extraction job status and results
 * 
 * @param jobId - The extraction job ID
 * @returns Query result with job status and entity counts
 */
export function useExtractionResults(jobId: string | null) {
  return useQuery<ExtractionResult, Error>({
    queryKey: QK.extraction.results(jobId || ''),
    queryFn: async () => {
      if (!jobId) throw new Error('No job ID provided');
      
      const response = await apiClient.get('l2', `/v1/extract/status/${jobId}`);
      return mapExtractionResult(response.data);
    },
    enabled: !!jobId,
    staleTime: STALE_TIME.poll,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if job is complete or failed
      if (data?.status === 'completed' || data?.status === 'failed' || data?.status === 'cancelled') {
        return false;
      }
      return 2000; // Poll every 2 seconds while running
    },
  });
}

/**
 * Get list of extracted entities for a job
 * 
 * Note: This is a placeholder that returns mock entities based on the
 * extraction status. In a full implementation, this would query a
 * dedicated endpoint for extracted entities.
 * 
 * @param jobId - The extraction job ID
 * @param count - Number of entities to return (from status response)
 * @returns Array of extracted entities for the table
 */
export function useExtractedEntities(jobId: string | null, count: number = 0) {
  return useQuery<ExtractedEntity[], Error>({
    queryKey: [...QK.extraction.results(jobId || ''), 'entities'],
    queryFn: async () => {
      if (!jobId || count === 0) return [];
      
      // NOTE: Using placeholder data until backend endpoint is available.
      // Backend ticket: L2-42 - Add GET /v1/extract/{job_id}/entities endpoint
      // When implemented, replace with: apiClient.get('l2', `/v1/extract/${jobId}/entities`)
      const entityTypes = ['Capability', 'UseCase', 'Persona', 'ValueDriver'];
      const mockEntities: ExtractedEntity[] = Array.from({ length: Math.min(count, 20) }, (_, i) => ({
        name: `Entity ${i + 1}`,
        type: entityTypes[i % entityTypes.length],
        confidence: 0.7 + Math.random() * 0.25,
        source: 'source-document.md',
        status: 'extracted',
      }));
      
      return mockEntities;
    },
    enabled: !!jobId && count > 0,
    staleTime: STALE_TIME.stats,
  });
}
