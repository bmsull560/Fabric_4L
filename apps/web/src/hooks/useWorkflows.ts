import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import { API_BASE, L4_PREFIX } from '@/lib/apiConfig';
import { POLL_INTERVALS } from './usePolling';
import { createFeatureLogger } from '@/lib/telemetry';

const log = createFeatureLogger('useWorkflows');

// Constants for workflow SSE
// POLL_INTERVAL_MS removed — use POLL_INTERVALS.workflows from usePolling
const SSE_TIMEOUT_MS = 30 * 1000;
const CANCEL_DELAY_MS = 500;

export interface Workflow {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  createdAt?: string;
  updatedAt?: string;
}


function normalizeWorkflowStatus(status: unknown): Workflow['status'] {
  const value = typeof status === 'string' ? status.toLowerCase() : '';
  if (value === 'pending' || value === 'running' || value === 'completed' || value === 'failed' || value === 'cancelled') {
    return value;
  }
  return 'pending';
}

function normalizeWorkflowProgress(rawProgress: unknown): number {
  const numeric = typeof rawProgress === 'number' ? rawProgress : Number(rawProgress);
  if (Number.isNaN(numeric)) {
    return 0;
  }
  return Math.min(100, Math.max(0, numeric));
}

interface RawWorkflow {
  workflow_id?: string;
  workflow_instance_id?: string;
  id?: string;
  name?: string;
  workflow_type?: string;
  status?: unknown;
  progress?: unknown;
  progress_percentage?: unknown;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
}

function normalizeWorkflow(raw: RawWorkflow): Workflow | null {
  const normalizedId = raw.workflow_id || raw.workflow_instance_id || raw.id;
  const normalizedIdText = String(normalizedId || '').trim();
  if (!normalizedIdText) {
    return null;
  }

  const normalizedName = raw.name || raw.workflow_type || 'workflow';
  const normalizedProgress = normalizeWorkflowProgress(raw.progress ?? raw.progress_percentage ?? 0);

  return {
    id: normalizedIdText,
    name: String(normalizedName),
    status: normalizeWorkflowStatus(raw.status),
    progress: normalizedProgress,
    createdAt: raw.createdAt || raw.created_at || raw.started_at,
    updatedAt: raw.updatedAt || raw.updated_at || raw.completed_at,
  };
}

function normalizeWorkflowList(data: unknown): Workflow[] {
  const normalized: Workflow[] = [];
  const seen = new Set<string>();

  for (const raw of extractWorkflowList(data)) {
    const workflow = normalizeWorkflow(raw);
    if (!workflow || seen.has(workflow.id)) {
      continue;
    }
    seen.add(workflow.id);
    normalized.push(workflow);
  }

  return normalized;
}

function extractWorkflowList(data: unknown): RawWorkflow[] {
  // Handle new paginated response format: { items: [...], total, limit, offset, has_more }
  if (data && typeof data === 'object' && Array.isArray((data as { items?: unknown[] }).items)) {
    return (data as { items: RawWorkflow[] }).items;
  }
  
  // Handle legacy array format
  if (Array.isArray(data)) {
    return data as RawWorkflow[];
  }

  // Handle legacy { workflows: [...] } format
  if (data && typeof data === 'object' && Array.isArray((data as { workflows?: unknown[] }).workflows)) {
    return (data as { workflows: RawWorkflow[] }).workflows;
  }

  return [];
}

// Pagination types for new API
export interface PaginatedWorkflows {
  items: Workflow[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Parse API response into PaginatedWorkflows structure.
 * Handles both new paginated format and legacy formats.
 */
function parsePaginatedResponse(data: unknown, items: Workflow[]): PaginatedWorkflows {
  // Check if response is already paginated
  if (data && typeof data === 'object' && 'items' in data && 'total' in data) {
    const paginated = data as PaginatedWorkflows;
    return {
      items,
      total: paginated.total,
      limit: paginated.limit,
      offset: paginated.offset,
      has_more: paginated.has_more,
    };
  }
  
  // Legacy fallback: treat all as single page
  return {
    items,
    total: items.length,
    limit: items.length,
    offset: 0,
    has_more: false,
  };
}

/**
 * Fetch and poll active workflows from Layer 4 with pagination support.
 * Polls every 5 seconds, stops on window focus (already polling).
 * 
 * @param limit - Maximum number of workflows to fetch (default: 50, max: 100)
 * @param offset - Number of workflows to skip for pagination (default: 0)
 * @param status - Optional status filter ('pending' | 'running' | 'completed' | 'failed' | 'cancelled')
 */
export function useActiveWorkflows(options: { limit?: number; offset?: number; status?: string } = {}) {
  const { limit = 50, offset = 0, status } = options;

  return useQuery<PaginatedWorkflows, Error>({
    queryKey: [...QK.workflows.active(), { limit, offset, status }],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('limit', String(limit));
      params.set('offset', String(offset));
      if (status) params.set('status', status);
      
      const response = await apiClient.get('l4', `/workflows/active?${params.toString()}`) as { data: unknown };
      const items = normalizeWorkflowList(response.data);
      return parsePaginatedResponse(response.data, items);
    },
    staleTime: STALE_TIME.poll,
    refetchInterval: POLL_INTERVALS.workflows,
    refetchOnWindowFocus: false, // Already polling, avoid duplicate fetches
  });
}

export function useWorkflowHistory(options: { limit?: number; offset?: number } = {}) {
  const { limit = 50, offset = 0 } = options;

  return useQuery<PaginatedWorkflows, Error>({
    queryKey: [...QK.workflows.history(), { limit, offset }],
    queryFn: async () => {
      // NOTE: Using /workflows/active with pagination params.
      // Backend now supports limit/offset for paginated workflow lists.
      const params = new URLSearchParams();
      params.set('limit', String(limit));
      params.set('offset', String(offset));
      
      const response = await apiClient.get('l4', `/workflows/active?${params.toString()}`) as { data: unknown };
      const items = normalizeWorkflowList(response.data);
      return parsePaginatedResponse(response.data, items);
    },
    staleTime: STALE_TIME.stats,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: { name: string; type: string; config?: Record<string, unknown> }) => {
      const response = await apiClient.post('l4', '/workflows', {
        name: params.name,
        workflow_type: params.type,
        config: params.config || {},
      }) as { data: Record<string, unknown> };
      const workflowId = response.data?.workflow_instance_id || response.data?.workflow_id;
      if (!workflowId) {
        throw new Error('Workflow creation response missing workflow id');
      }
      return String(workflowId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.workflows.active() });
      queryClient.invalidateQueries({ queryKey: QK.workflows.history() });
    },
  });
}

/**
 * Cancel a running workflow and refresh the workflow lists.
 * Includes a brief delay to allow backend state propagation.
 */
export function useCancelWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete('l4', `/workflows/${id}`);
    },
    onSuccess: async () => {
      // Brief delay to allow backend to process cancellation
      // before refetching to avoid stale "running" state
      await new Promise((resolve) => setTimeout(resolve, CANCEL_DELAY_MS));
      await queryClient.invalidateQueries({ queryKey: QK.workflows.active() });
      await queryClient.invalidateQueries({ queryKey: QK.workflows.history() });
    },
  });
}

/**
 * Subscribe to workflow updates via Server-Sent Events.
 * Uses useEffect for proper cleanup guarantee when component unmounts.
 */
export function useWorkflowSSE(workflowId: string | null) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!workflowId) {
      setWorkflow(null);
      setError(null);
      setIsConnected(false);
      return;
    }

    const url = `${API_BASE}${L4_PREFIX}/workflows/${workflowId}/events`;

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(url);
    eventSourceRef.current = es;
    setIsConnected(true);
    setError(null);

    // Set up timeout
    timeoutRef.current = setTimeout(() => {
      if (eventSourceRef.current === es) {
        es.close();
        eventSourceRef.current = null;
        setIsConnected(false);
        setError(new Error(`SSE connection timeout after ${SSE_TIMEOUT_MS / 1000}s`));
      }
    }, SSE_TIMEOUT_MS);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.payload) {
          const normalized = normalizeWorkflow(data.payload);
          if (normalized) {
            setWorkflow(normalized);
            // Keep connection open for ongoing updates, don't close
          }
        }
      } catch (err) {
        // Log parse errors for debugging but don't break the connection
        log.warn('Failed to parse SSE message', { errorCode: String(err) });
      }
    };

    es.onerror = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (eventSourceRef.current === es) {
        setIsConnected(false);
        setError(new Error('SSE connection failed'));
      }
      es.close();
    };

    // Cleanup function - guaranteed to run on unmount
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      es.close();
      if (eventSourceRef.current === es) {
        eventSourceRef.current = null;
        setIsConnected(false);
      }
    };
  }, [workflowId]);

  return { workflow, error, isConnected };
}

/**
 * Pause a running workflow.
 * POST /workflows/{id}/pause
 */
export function usePauseWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post('l4', `/workflows/${id}/pause`, {});
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QK.workflows.active() });
    },
  });
}

/**
 * Resume a paused workflow.
 * POST /workflows/{id}/resume
 */
export function useResumeWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post('l4', `/workflows/${id}/resume`, {});
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QK.workflows.active() });
    },
  });
}

/**
 * Get detailed workflow state including performance metrics.
 * GET /workflows/{id}
 */
export function useWorkflowDetail(workflowId: string | null) {
  return useQuery({
    queryKey: QK.workflows.detail(workflowId ?? ''),
    queryFn: async () => {
      const response = await apiClient.get('l4', `/workflows/${workflowId}`) as { data: unknown };
      return response.data as Workflow & {
        result?: unknown;
        checkpoints?: { id: string; created_at: string }[];
      };
    },
    enabled: !!workflowId,
    staleTime: 5_000,
  });
}

/**
 * Get available workflow types.
 * GET /workflows/types
 */
export function useWorkflowTypes() {
  return useQuery({
    queryKey: [...QK.workflows.all, 'types'],
    queryFn: async () => {
      const response = await apiClient.get('l4', '/workflows/types') as { data: unknown };
      return response.data as { types: { id: string; name: string; description: string }[] };
    },
    staleTime: 60_000,
  });
}
