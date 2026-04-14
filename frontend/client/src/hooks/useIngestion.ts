import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import { POLL_INTERVALS } from './usePolling';
import { parseIngestionAggregation, parseIngestionJobs, type ApiIngestionJobDto } from '@/types/api';

export interface IngestionJob {
  id: string;
  domain: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  pagesFound?: number;
  pagesProcessed?: number;
  createdAt: string;
  updatedAt?: string;
  completedAt?: string;
}

export interface IngestionStats {
  totalDomains: number;
  pagesSynthesized: number;
  sourcesAnalyzed: number;
  avgProcessingTime: number;
}


function mapIngestionJob(job: ApiIngestionJobDto): IngestionJob {
  return {
    id: job.id || 'unknown',
    domain: job.configuration?.url || 'unknown',
    status: mapJobStatus(job.status || ''),
    progress: job.progress_percent_complete ?? 0,
    pagesProcessed: job.progress_processed_pages ?? 0,
    createdAt: job.created_at || new Date(0).toISOString(),
    updatedAt: job.started_at || job.updated_at || job.created_at || new Date(0).toISOString(),
  };
}

export function useIngestionJobs() {
  return useQuery({
    queryKey: QK.ingestion.jobs(),
    queryFn: async () => {
      const response = await apiClient.get('l1', '/jobs');
      const jobs = parseIngestionJobs(response.data?.data);
      return jobs.map(mapIngestionJob);
    },
    staleTime: STALE_TIME.poll,
  });
}

export function useRecentIngestionJobs(limit = 5) {
  return useQuery({
    queryKey: QK.ingestion.recent(),
    queryFn: async () => {
      const response = await apiClient.get('l1', `/jobs?limit=${limit}&sort_by=created_at&sort_order=desc`);
      const jobs = parseIngestionJobs(response.data?.data);
      return jobs.map(mapIngestionJob);
    },
    staleTime: STALE_TIME.poll,
    refetchInterval: POLL_INTERVALS.ingestion,
  });
}

// Map backend job status to frontend status
function mapJobStatus(status: string): IngestionJob['status'] {
  const statusMap: Record<string, IngestionJob['status']> = {
    'PENDING': 'pending',
    'QUEUED': 'pending',
    'VALIDATING': 'processing',
    'BROWSER_ACQUIRING': 'processing',
    'NAVIGATING': 'processing',
    'EXTRACTING': 'processing',
    'TRANSFORMING': 'processing',
    'STORING': 'processing',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'failed',
    'PARTIAL_SUCCESS': 'completed',
  };
  return statusMap[status] || 'pending';
}

export function useIngestionStats() {
  return useQuery({
    queryKey: QK.ingestion.stats(),
    queryFn: async () => {
      const response = await apiClient.get('l1', '/jobs?limit=1');
      const agg = parseIngestionAggregation(response.data?.aggregation);
      const byStatus = agg.by_status || {};
      return {
        totalDomains: Object.values(byStatus).reduce((a, b) => a + b, 0),
        pagesSynthesized: agg.total_records_extracted ?? 0,
        sourcesAnalyzed: Object.keys(byStatus).length,
        avgProcessingTime: agg.total_execution_time_ms ?? 0,
      };
    },
    staleTime: STALE_TIME.stats,
  });
}

export function useSubmitDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (domain: string) => {
      const url = domain.startsWith('http') ? domain : `https://${domain}`;

      // Step 1: Create a scraping target with the domain URL
      const targetResponse = await apiClient.post('l1', '/targets', {
        name: domain,
        url,
      });
      const targetId = targetResponse.data.id as string;

      // Step 2: Execute the target to start the ingestion job
      const executeResponse = await apiClient.post('l1', `/targets/${targetId}/execute`, {});
      return executeResponse.data.job_id as string;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ingestion.recent() });
      queryClient.invalidateQueries({ queryKey: QK.ingestion.stats() });
    },
  });
}
