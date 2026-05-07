import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface WorkflowSessionContext {
  accountId: string | null;
  caseId: string | null;
  selectedEntityId: string | null;
  tabId: string | null;
  lastPath: string | null;
  updatedAt: string | null;
}

interface WorkflowSessionState {
  context: WorkflowSessionContext;
  setContext: (next: Partial<WorkflowSessionContext>) => void;
  clearContext: () => void;
}

const EMPTY_CONTEXT: WorkflowSessionContext = {
  accountId: null,
  caseId: null,
  selectedEntityId: null,
  tabId: null,
  lastPath: null,
  updatedAt: null,
};

export const useWorkflowSessionStore = create<WorkflowSessionState>()(
  persist(
    (set) => ({
      context: EMPTY_CONTEXT,
      setContext: (next) =>
        set((state) => ({
          context: {
            ...state.context,
            ...next,
            updatedAt: new Date().toISOString(),
          },
        })),
      clearContext: () => set({ context: EMPTY_CONTEXT }),
    }),
    {
      name: "fabric-workflow-session-context",
      partialize: (state) => ({ context: state.context }),
    }
  )
);
