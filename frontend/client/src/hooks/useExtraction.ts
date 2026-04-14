import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { parseExtractionJob } from '@/types/api';

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

// Color mapping for entity type chips
const ENTITY_CHIP_COLORS: Record<string, string> = {
  outcome: 'text-emerald-400',
  capability: 'text-blue-400',
  usecase: 'text-purple-400',
  persona: 'text-amber-400',
  valuedriver: 'text-rose-400',
  default: 'text-neutral-400',
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
      const job = parseExtractionJob(response.data);

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
      const backendStatus = job.status || 'PENDING';
      const isDone = (statuses: string[]) => statuses.includes(backendStatus);
      const isTerminal = isDone(['COMPLETED', 'FAILED', 'CANCELLED']);

      const steps: ExtractionStep[] = [
        {
          id: 1,
          label: 'Crawling',
          sub: `Acquired ${job.progress_pages_found ?? 0} nodes from domain.`,
          done: isTerminal || isDone(['EXTRACTING', 'TRANSFORMING', 'STORING']),
          active: isDone(['NAVIGATING', 'BROWSER_ACQUIRING']),
          pct: backendStatus === 'NAVIGATING' && (job.progress_pages_found ?? 0) > 0
            ? Math.min(100, ((job.progress_processed_pages ?? 0) / (job.progress_pages_found ?? 1)) * 100)
            : undefined,
        },
        {
          id: 2,
          label: 'NER Extraction',
          sub: 'Identifying entities, capabilities, and outcomes.',
          done: isTerminal || isDone(['TRANSFORMING', 'STORING']),
          active: backendStatus === 'EXTRACTING',
          pct: backendStatus === 'EXTRACTING'
            ? Math.min(100, job.progress_percent_complete ?? 0)
            : undefined,
        },
        {
          id: 3,
          label: 'Semantic Mapping',
          sub: '',
          done: isTerminal || isDone(['STORING']),
          active: backendStatus === 'TRANSFORMING',
        },
        {
          id: 4,
          label: 'Fabric Assembly',
          sub: '',
          done: backendStatus === 'COMPLETED',
          active: backendStatus === 'STORING',
        },
      ];

      // Parse logs from job progress
      const logs: LogLine[] = (job.progress_logs || []).map((log) => ({
        t: log.timestamp ? new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) : null,
        type: mapLogType(log.level || 'info'),
        text: log.message || '',
        extra: log.status,
        extraColor: log.status === 'OK' ? 'text-emerald-400' : undefined,
      }));

      // Build entity chips from extracted entities
      const entitiesFound: EntityChip[] = (job.extracted_entities || []).map((entity) => {
        const entityType = entity.type || 'unknown';
        return {
          label: `${entityType}: ${entity.name || 'Unknown'}`,
          color: ENTITY_CHIP_COLORS[entityType] || ENTITY_CHIP_COLORS.default,
        };
      });

      return {
        id: job.id || jobId,
        domain: job.configuration?.url || 'unknown',
        status: statusMap[backendStatus] || 'pending',
        progress: job.progress_percent_complete ?? 0,
        steps,
        logs,
        entitiesFound,
        createdAt: job.created_at,
        updatedAt: job.updated_at,
      };
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
