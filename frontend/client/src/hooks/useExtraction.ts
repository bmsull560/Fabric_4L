import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface ExtractionJob {
  id: string;
  domain: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  steps: ExtractionStep[];
  logs: LogLine[];
  entitiesFound: EntityChip[];
  createdAt?: string;
  updatedAt?: string;
}

export interface ExtractionStep {
  id: number;
  label: string;
  sub?: string;
  done: boolean;
  active: boolean;
  pct?: number;
}

export interface LogLine {
  t: string | null;
  type: 'sys' | 'info' | 'warn' | 'extract' | 'map' | 'plain';
  text: string;
  link?: string;
  conf?: string;
  extra?: string;
  extraColor?: string;
}

export interface EntityChip {
  label: string;
  color: string;
}

const EXTRACTION_KEYS = {
  all: ['extraction'] as const,
  job: (id: string) => [...EXTRACTION_KEYS.all, 'job', id] as const,
};

const TYPE_COLORS: Record<string, string> = {
  sys: 'text-neutral-400',
  info: 'text-cyan-400',
  warn: 'text-amber-400',
  extract: 'text-neutral-300',
  map: 'text-neutral-300',
  plain: 'text-neutral-400',
};

const TYPE_LABELS: Record<string, string> = {
  sys: '[SYS]', info: '[INFO]', warn: '[WARN]', extract: '[EXTRACT]', map: '[MAP]', plain: '',
};

/**
 * Get extraction job status from L2 API
 */
export function useExtractionJob(jobId: string | null) {
  return useQuery({
    queryKey: EXTRACTION_KEYS.job(jobId || ''),
    queryFn: async () => {
      if (!jobId) throw new Error('No job ID provided');

      // Query L2 for job status
      const response = await apiClient.get('l2', `/jobs/${jobId}`);
      const job = response.data;

      // Map backend status to frontend status
      const statusMap: Record<string, ExtractionJob['status']> = {
        'PENDING': 'pending',
        'QUEUED': 'pending',
        'VALIDATING': 'running',
        'BROWSER_ACQUIRING': 'running',
        'NAVIGATING': 'running',
        'EXTRACTING': 'running',
        'TRANSFORMING': 'running',
        'STORING': 'running',
        'COMPLETED': 'completed',
        'FAILED': 'failed',
        'CANCELLED': 'cancelled',
        'PARTIAL_SUCCESS': 'completed',
      };

      // Build steps from job phases
      const steps: ExtractionStep[] = [
        { id: 1, label: 'Crawling', sub: `Acquired ${job.progress_pages_found || 0} nodes from domain.`, done: ['COMPLETED', 'FAILED', 'CANCELLED'].includes(job.status) || ['EXTRACTING', 'TRANSFORMING', 'STORING'].includes(job.status), active: job.status === 'NAVIGATING' || job.status === 'BROWSER_ACQUIRING', pct: job.status === 'NAVIGATING' ? Math.min(100, (job.progress_processed_pages / job.progress_pages_found) * 100) : undefined },
        { id: 2, label: 'NER Extraction', sub: 'Identifying entities, capabilities, and outcomes.', done: ['COMPLETED', 'FAILED', 'CANCELLED'].includes(job.status) || ['TRANSFORMING', 'STORING'].includes(job.status), active: job.status === 'EXTRACTING', pct: job.status === 'EXTRACTING' ? Math.min(100, job.progress_percent_complete || 0) : undefined },
        { id: 3, label: 'Semantic Mapping', sub: '', done: ['COMPLETED', 'FAILED', 'CANCELLED'].includes(job.status) || ['STORING'].includes(job.status), active: job.status === 'TRANSFORMING' },
        { id: 4, label: 'Fabric Assembly', sub: '', done: job.status === 'COMPLETED', active: job.status === 'STORING' },
      ];

      // Parse logs from job progress
      const logs: LogLine[] = job.progress_logs?.map((log: any, index: number) => ({
        t: log.timestamp ? new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) : null,
        type: mapLogType(log.level || 'info'),
        text: log.message,
        extra: log.status,
        extraColor: log.status === 'OK' ? 'text-emerald-400' : undefined,
      })) || [];

      // Build entity chips from extracted entities
      const entitiesFound: EntityChip[] = job.extracted_entities?.map((e: any) => ({
        label: `${e.type}: ${e.name}`,
        color: e.type === 'Outcome' ? 'bg-emerald-900/40 text-emerald-300 border-emerald-700' :
               e.type === 'Capability' ? 'bg-violet-900/40 text-violet-300 border-violet-700' :
               'bg-neutral-900/40 text-neutral-300 border-neutral-700',
      })) || [];

      return {
        id: job.id,
        domain: job.configuration?.url || 'unknown',
        status: statusMap[job.status] || 'pending',
        progress: job.progress_percent_complete || 0,
        steps,
        logs,
        entitiesFound,
        createdAt: job.created_at,
        updatedAt: job.updated_at,
      } as ExtractionJob;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if job is complete or failed
      if (data?.status === 'completed' || data?.status === 'failed' || data?.status === 'cancelled') {
        return false;
      }
      return 2000; // Poll every 2 seconds while running
    },
    staleTime: 1000,
  });
}

function mapLogType(level: string): LogLine['type'] {
  const typeMap: Record<string, LogLine['type']> = {
    'DEBUG': 'plain',
    'INFO': 'info',
    'WARNING': 'warn',
    'ERROR': 'warn',
    'CRITICAL': 'warn',
  };
  return typeMap[level.toUpperCase()] || 'plain';
}

export { TYPE_COLORS, TYPE_LABELS };
