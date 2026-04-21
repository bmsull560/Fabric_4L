import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ProspectInfo, EnrichedEntity } from '../types';
import { WORKFLOW_STORAGE_KEY, SESSION_ID } from '../constants';

/**
 * Generate a cryptographically secure session ID
 * Falls back to Math.random() in environments without crypto API
 */
function generateSessionId(): string {
  const timestamp = Date.now().toString(36);
  let randomPart: string;

  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    const array = new Uint8Array(SESSION_ID.RANDOM_BYTES);
    crypto.getRandomValues(array);
    randomPart = Array.from(array, (b) => (b % 36).toString(36)).join('');
  } else {
    randomPart = Math.random().toString(36).slice(2, 2 + SESSION_ID.RANDOM_BYTES);
  }

  return `${SESSION_ID.PREFIX}_${timestamp}_${randomPart}`;
}

export interface WorkflowState {
  sessionId: string | null;
  currentStep: number;
  prospect: ProspectInfo | null;
  enrichedEntities: EnrichedEntity[];
  selectedTreeId: string | null;
  generatedCaseId: string | null;
}

export interface WorkflowActions {
  /** Initialize a new workflow session with generated ID */
  initSession: () => void;
  /** Reset entire workflow state to initial values */
  reset: () => void;
  /** Set current step index (0-6) */
  setCurrentStep: (step: number) => void;
  /** Store prospect information */
  setProspect: (prospect: ProspectInfo) => void;
  /** Store enriched entities from intelligence step */
  setEnrichedEntities: (entities: EnrichedEntity[]) => void;
  /** Store selected value driver tree ID */
  setSelectedTreeId: (id: string | null) => void;
  /** Store generated value case ID */
  setGeneratedCaseId: (id: string | null) => void;
}

const initialState: WorkflowState = {
  sessionId: null,
  currentStep: 0,
  prospect: null,
  enrichedEntities: [],
  selectedTreeId: null,
  generatedCaseId: null,
};

export const useWorkflowStore = create<WorkflowState & WorkflowActions>()(
  persist(
    (set) => ({
      ...initialState,
      initSession: () => set({
        ...initialState,
        sessionId: generateSessionId(),
      }),
      reset: () => set(initialState),
      setCurrentStep: (step) => set({ currentStep: step }),
      setProspect: (prospect) => set({ prospect }),
      setEnrichedEntities: (entities) => set({ enrichedEntities: entities }),
      setSelectedTreeId: (id) => set({ selectedTreeId: id }),
      setGeneratedCaseId: (id) => set({ generatedCaseId: id }),
    }),
    { name: WORKFLOW_STORAGE_KEY }
  )
);
