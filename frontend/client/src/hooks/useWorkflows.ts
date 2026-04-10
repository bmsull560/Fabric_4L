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

export function useActiveWorkflows() {
  return useQuery({
    queryKey: WORKFLOW_KEYS.active(),
    queryFn: async () => {
      const response = await apiClient.get('l4', '/workflows/active');
      return (response.data || []) as Workflow[];
    },
    staleTime: 30 * 1000,
    refetchInterval: 5000,
  });
}

export function useWorkflowHistory() {
  return useQuery({
    queryKey: WORKFLOW_KEYS.history(),
    queryFn: async () => {
      const response = await apiClient.get('l4', '/workflows/active');
      return (response.data || []) as Workflow[];
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
      return response.data.workflow_instance_id || response.data.workflow_id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WORKFLOW_KEYS.active() });
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

        const eventSource = new EventSource(`/api/v1/agents/workflows/${workflowId}/events`);
        let resolved = false;

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.payload?.workflow_id && data.payload?.status) {
              if (!resolved) {
                resolved = true;
                resolve(data.payload as Workflow);
              }
            }
          } catch {
            // Ignore invalid JSON
          }
        };

        eventSource.onerror = () => {
          if (!resolved) {
            reject(new Error('SSE connection failed'));
          }
          eventSource.close();
        };

        setTimeout(() => {
          if (!resolved) {
            eventSource.close();
          }
        }, 30000);
      });
    },
    enabled: !!workflowId,
    staleTime: Infinity,
  });
}
