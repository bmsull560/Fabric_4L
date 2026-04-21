/**
 * Workflow Constants
 * Centralized configuration for the 7-step value creation workflow
 */

/** Analysis simulation delay in milliseconds */
export const ANALYSIS_DELAY_MS = 1500;

/** Session storage key for Zustand persist middleware */
export const WORKFLOW_STORAGE_KEY = 'workflow-session';

/** Minimum input lengths for validation */
export const VALIDATION = {
  MIN_COMPANY_NAME_LENGTH: 2,
  MIN_CONTACT_NAME_LENGTH: 2,
  MAX_COMPANY_NAME_LENGTH: 100,
  MAX_CONTACT_NAME_LENGTH: 100,
  MAX_TITLE_LENGTH: 100,
} as const;

/** Session ID generation config */
export const SESSION_ID = {
  PREFIX: 'wf',
  RANDOM_BYTES: 9, // Base36 encoding produces ~11 chars from 9 bytes
} as const;

/** Workflow step index constants for type safety */
export const STEPS = {
  PROSPECT: 0,
  INTELLIGENCE: 1,
  AI_MODEL: 2,
  DRIVER_TREE: 3,
  EVIDENCE: 4,
  CALCULATOR: 5,
  VALUE_CASE: 6,
} as const;

/** Mock simulation delays for development/testing */
export const SIMULATION = {
  SEARCH_DELAY_MS: 1000,
  ENTITY_CONFIDENCE_MIN: 0.85,
  ENTITY_CONFIDENCE_MAX: 0.95,
} as const;
