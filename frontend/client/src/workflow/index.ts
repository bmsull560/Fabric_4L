/**
 * Workflow Module
 *
 * Guided 7-step value-case creation workflow.
 * Runs parallel to Value Studio as an alternative guided experience.
 */

// Constants
export {
  ANALYSIS_DELAY_MS,
  WORKFLOW_STORAGE_KEY,
  VALIDATION,
  SESSION_ID,
  STEPS,
  SIMULATION,
} from './constants';

// Types
export type {
  ProspectInfo,
  EnrichedEntity,
  WorkflowStep,
} from './types';
export { WORKFLOW_STEPS } from './types';

// Store
export { useWorkflowStore } from './store/workflowStore';
export type { WorkflowState } from './store/workflowStore';

// Components
export { StepCard } from './components/StepCard';
export { WorkflowLayout } from './components/WorkflowLayout';
