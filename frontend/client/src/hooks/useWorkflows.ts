import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { apiClient } from '@/api/client';

// Constants for workflow polling and SSE
const POLL_INTERVAL_MS = 5000;
const STALE_TIME_MS = 30 * 1000;
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

const WORKFLOW_KEYS = {
  all: ['workflows'] as const,
  active: () => [...WORKFLOW_KEYS.all, 'active'] as const,
  history: () => [...WORKFLOW_KEYS.all, 'history'] as const,
  detail: (id: string) => [...WORKFLOW_KEYS.all, 'detail', id] as const,
};

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
  if (Array.isArray(data)) {
    return data as RawWorkflow[];
  }

  if (data && typeof data === 'object' && Array.isArray((data as { workflows?: unknown[] }).workflows)) {
    return (data as { workflows: RawWorkflow[] }).workflows;
  }

  return [];
}

/**
 * Fetch and poll active workflows from Layer 4.
 * Polls every 5 seconds, stops on window focus (already polling).
 */
export function useActiveWorkflows() {
  return useQuery({
    queryKey: WORKFLOW_KEYS.active(),
    queryFn: async () => {
      const response = await apiClient.get('l4', '/workflows/active');
      return normalizeWorkflowList(response.data);
    },
    staleTime: STALE_TIME_MS,
    refetchInterval: POLL_INTERVAL_MS,
    refetchOnWindowFocus: false, // Already polling, avoid duplicate fetches
  });
}

export function useWorkflowHistory() {
  return useQuery({
    queryKey: WORKFLOW_KEYS.history(),
    queryFn: async () => {
      // NOTE: Currently using /workflows/active as a proxy for history.
      // When Layer 4 adds GET /workflows with pagination, update this to use
      // the paginated endpoint with proper limit/offset parameters.
      const response = await apiClient.get('l4', '/workflows/active');
      return normalizeWorkflowList(response.data);
    },
    staleTime: 60 * 1000,
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
      });
      const workflowId = response.data?.workflow_instance_id || response.data?.workflow_id;
      if (!workflowId) {
        throw new Error('Workflow creation response missing workflow id');
      }
      return String(workflowId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.active() });
      queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.history() });
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
      await queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.active() });
      await queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.history() });
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

    const baseUrl = import.meta.env.VITE_API_BASE || '/api/v1';
    const l4Prefix = import.meta.env.VITE_L4_PREFIX || '/agents';
    const url = `${baseUrl}${l4Prefix}/workflows/${workflowId}/events`;

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
        console.warn('[WorkflowSSE] Failed to parse SSE message:', err);
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
