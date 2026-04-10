import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

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

function normalizeWorkflow(raw: any): Workflow | null {
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

function extractWorkflowList(data: unknown): any[] {
  if (Array.isArray(data)) {
    return data;
  }

  if (data && typeof data === 'object' && Array.isArray((data as { workflows?: unknown[] }).workflows)) {
    return (data as { workflows: unknown[] }).workflows;
  }

  return [];
}

export function useActiveWorkflows() {
  return useQuery({
    queryKey: WORKFLOW_KEYS.active(),
    queryFn: async () => {
      const response = await apiClient.get('l4', '/workflows/active');
      return normalizeWorkflowList(response.data);
    },
    staleTime: 30 * 1000,
    refetchInterval: 5000,
  });
}

export function useWorkflowHistory() {
  return useQuery({
    queryKey: WORKFLOW_KEYS.history(),
    queryFn: async () => {
      // TODO: Switch to paginated GET /workflows when Layer 4 exposes a list-all endpoint.
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

export function useCancelWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete('l4', `/workflows/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.active() });
      queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.history() });
    },
  });
}

export function useWorkflowSSE(workflowId: string | null) {
  return useQuery({
    queryKey: [...WORKFLOW_KEYS.all, 'sse', workflowId],
    queryFn: () => {
      return new Promise<Workflow>((resolve, reject) => {
        if (!workflowId) {
          reject(new Error('No workflow ID provided'));
          return;
        }

        const baseUrl = import.meta.env.VITE_API_BASE || '/api/v1';
        const l4Prefix = import.meta.env.VITE_L4_PREFIX || '/agents';
        const eventSource = new EventSource(`${baseUrl}${l4Prefix}/workflows/${workflowId}/events`);
        let resolved = false;
        const timeoutId = setTimeout(() => {
          if (!resolved) {
            resolved = true;
            eventSource.close();
            reject(new Error('SSE connection timeout after 30s'));
          }
        }, 30000);

        const resolveOnce = (workflow: Workflow) => {
          if (resolved) return;
          resolved = true;
          clearTimeout(timeoutId);
          eventSource.close();
          resolve(workflow);
        };

        const rejectOnce = (error: Error) => {
          if (resolved) return;
          resolved = true;
          clearTimeout(timeoutId);
          eventSource.close();
          reject(error);
        };

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.payload) {
              const normalized = normalizeWorkflow(data.payload);
              if (normalized) {
                resolveOnce(normalized);
              }
            }
          } catch {
            // Ignore invalid JSON
          }
        };

        eventSource.onerror = () => {
          rejectOnce(new Error('SSE connection failed'));
        };
      });
    },
    enabled: !!workflowId,
    staleTime: Infinity,
    retry: false,
  });
}
