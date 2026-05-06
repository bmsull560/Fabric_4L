/**
 * useWizard — Shared primitive for multi-step workflow pages with draft persistence
 *
 * Provides:
 * - Step navigation (next, previous, goTo)
 * - Draft persistence via localStorage
 * - Step validation tracking
 * - Session management
 * - Input validation for configuration
 *
 * Usage:
 * ```tsx
 * const { currentStep, nextStep, prevStep, goToStep, canProceed, saveDraft, loadDraft, clearDraft } = useWizard({
 *   totalSteps: 5,
 *   storageKey: 'my-workflow-draft',
 *   initialStep: 0,
 * });
 * ```
 *
 * @throws {Error} If totalSteps is not positive
 * @throws {Error} If initialStep is out of bounds [0, totalSteps - 1]
 */

import { useState, useCallback, useEffect } from 'react';

export interface UseWizardOptions {
  totalSteps: number;
  storageKey: string;
  initialStep?: number;
  autoSave?: boolean;
}

export interface UseWizardReturn {
  // State
  currentStep: number;
  canGoNext: boolean;
  canGoPrev: boolean;
  isComplete: boolean;
  stepValidation: Record<number, boolean>;

  // Navigation
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: number) => void;
  reset: () => void;

  // Validation
  validateStep: (step: number, isValid: boolean) => void;
  canProceed: boolean;

  // Draft persistence
  saveDraft: (data: Record<string, unknown>) => void;
  loadDraft: () => Record<string, unknown> | null;
  clearDraft: () => void;

  // Session
  sessionId: string;
}

const generateSessionId = (): string => {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).slice(2, 11);
  return `wizard_${timestamp}_${randomPart}`;
};

export function useWizard(options: UseWizardOptions): UseWizardReturn {
  const {
    totalSteps,
    storageKey,
    initialStep = 0,
    autoSave = true,
  } = options;

  // Validate inputs
  if (totalSteps <= 0) {
    throw new Error(`useWizard: totalSteps must be positive, received ${totalSteps}`);
  }
  if (initialStep < 0 || initialStep >= totalSteps) {
    throw new Error(`useWizard: initialStep must be between 0 and ${totalSteps - 1}, received ${initialStep}`);
  }

  const [currentStep, setCurrentStep] = useState(initialStep);
  const [stepValidation, setStepValidation] = useState<Record<number, boolean>>({});
  const [sessionId] = useState(generateSessionId());

  // Load draft on mount
  useEffect(() => {
    if (autoSave) {
      const saved = loadDraftFromStorage(storageKey);
      if (saved && typeof saved === 'object' && 'currentStep' in saved) {
        setCurrentStep((saved.currentStep as number) ?? initialStep);
        if (saved.stepValidation) {
          setStepValidation(saved.stepValidation as Record<number, boolean>);
        }
      }
    }
  }, [storageKey, initialStep, autoSave]);

  // Auto-save draft on step change
  useEffect(() => {
    if (autoSave) {
      saveDraftToStorage(storageKey, {
        currentStep,
        stepValidation,
        sessionId,
        savedAt: new Date().toISOString(),
      });
    }
  }, [currentStep, stepValidation, sessionId, storageKey, autoSave]);

  const canGoNext = currentStep < totalSteps - 1;
  const canGoPrev = currentStep > 0;
  const isComplete = currentStep === totalSteps - 1;

  const canProceed = stepValidation[currentStep] !== false;

  const nextStep = useCallback(() => {
    if (canGoNext && canProceed) {
      setCurrentStep((prev) => prev + 1);
    }
  }, [canGoNext, canProceed]);

  const prevStep = useCallback(() => {
    if (canGoPrev) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [canGoPrev]);

  const goToStep = useCallback((step: number) => {
    const validStep = Math.max(0, Math.min(step, totalSteps - 1));
    setCurrentStep(validStep);
  }, [totalSteps]);

  const reset = useCallback(() => {
    setCurrentStep(initialStep);
    setStepValidation({});
    clearDraftFromStorage(storageKey);
  }, [initialStep, storageKey]);

  const validateStep = useCallback((step: number, isValid: boolean) => {
    setStepValidation((prev) => ({
      ...prev,
      [step]: isValid,
    }));
  }, []);

  const saveDraft = useCallback((data: Record<string, unknown>) => {
    saveDraftToStorage(storageKey, {
      ...data,
      currentStep,
      stepValidation,
      sessionId,
      savedAt: new Date().toISOString(),
    });
  }, [storageKey, currentStep, stepValidation, sessionId]);

  const loadDraft = useCallback(() => {
    return loadDraftFromStorage(storageKey);
  }, [storageKey]);

  const clearDraft = useCallback(() => {
    clearDraftFromStorage(storageKey);
  }, [storageKey]);

  return {
    currentStep,
    canGoNext,
    canGoPrev,
    isComplete,
    stepValidation,
    nextStep,
    prevStep,
    goToStep,
    reset,
    validateStep,
    canProceed,
    saveDraft,
    loadDraft,
    clearDraft,
    sessionId,
  };
}

// ── Storage Helpers ─────────────────────────────────────────────────────────

function saveDraftToStorage(key: string, data: Record<string, unknown>): void {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.warn(`Failed to save draft to localStorage (key: ${key}):`, error);
  }
}

function loadDraftFromStorage(key: string): Record<string, unknown> | null {
  try {
    const item = localStorage.getItem(key);
    if (!item) return null;
    return JSON.parse(item);
  } catch (error) {
    console.warn(`Failed to load draft from localStorage (key: ${key}):`, error);
    return null;
  }
}

function clearDraftFromStorage(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Failed to clear draft from localStorage (key: ${key}):`, error);
  }
}
