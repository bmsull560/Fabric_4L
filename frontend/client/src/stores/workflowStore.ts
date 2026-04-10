import { create } from 'zustand';

export interface Workflow {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * Workflow UI State Store
 * ONLY client/UI state - no server state (use React Query for that)
 */
interface WorkflowUIState {
  selectedWorkflow: Workflow | null;
  sseConnected: boolean;

  selectWorkflow: (workflow: Workflow | null) => void;
  setSSEConnected: (connected: boolean) => void;
}

export const useWorkflowUIStore = create<WorkflowUIState>((set) => ({
  selectedWorkflow: null,
  sseConnected: false,

  selectWorkflow: (workflow) => set({ selectedWorkflow: workflow }),
  setSSEConnected: (connected) => set({ sseConnected: connected }),
}));

