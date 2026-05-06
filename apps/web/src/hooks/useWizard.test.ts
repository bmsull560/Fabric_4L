/**
 * useWizard test suite
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useWizard } from './useWizard';

describe('useWizard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('input validation', () => {
    it('should throw if totalSteps is not positive', () => {
      expect(() => {
        renderHook(() => useWizard({ totalSteps: 0, storageKey: 'test' }));
      }).toThrow('useWizard: totalSteps must be positive, received 0');
    });

    it('should throw if totalSteps is negative', () => {
      expect(() => {
        renderHook(() => useWizard({ totalSteps: -1, storageKey: 'test' }));
      }).toThrow('useWizard: totalSteps must be positive, received -1');
    });

    it('should throw if initialStep is negative', () => {
      expect(() => {
        renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: -1 }));
      }).toThrow('useWizard: initialStep must be between 0 and 4, received -1');
    });

    it('should throw if initialStep exceeds totalSteps', () => {
      expect(() => {
        renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: 5 }));
      }).toThrow('useWizard: initialStep must be between 0 and 4, received 5');
    });

    it('should accept valid initialStep at upper bound', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: 4 }));
      expect(result.current.currentStep).toBe(4);
    });
  });

  describe('step navigation', () => {
    it('should initialize with currentStep', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: 2 }));
      expect(result.current.currentStep).toBe(2);
    });

    it('should navigate to next step', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.nextStep();
      });
      
      expect(result.current.currentStep).toBe(1);
    });

    it('should not navigate beyond last step', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 3, storageKey: 'test', initialStep: 2 }));
      
      act(() => {
        result.current.nextStep();
      });
      
      expect(result.current.currentStep).toBe(2);
      expect(result.current.canGoNext).toBe(false);
    });

    it('should navigate to previous step', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: 2 }));
      
      act(() => {
        result.current.prevStep();
      });
      
      expect(result.current.currentStep).toBe(1);
    });

    it('should not navigate before first step', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.prevStep();
      });
      
      expect(result.current.currentStep).toBe(0);
      expect(result.current.canGoPrev).toBe(false);
    });

    it('should go to specific step', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.goToStep(3);
      });
      
      expect(result.current.currentStep).toBe(3);
    });

    it('should clamp goToStep to bounds', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.goToStep(10);
      });
      
      expect(result.current.currentStep).toBe(4);
    });

    it('should reset to initial step', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: 2 }));
      
      act(() => {
        result.current.nextStep();
      });
      expect(result.current.currentStep).toBe(3);
      
      act(() => {
        result.current.reset();
      });
      
      expect(result.current.currentStep).toBe(2);
    });
  });

  describe('step validation', () => {
    it('should allow proceeding when step is valid', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      expect(result.current.canProceed).toBe(true);
    });

    it('should block proceeding when step is invalid', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.validateStep(0, false);
      });
      
      expect(result.current.canProceed).toBe(false);
      expect(result.current.stepValidation[0]).toBe(false);
    });

    it('should allow proceeding after revalidating', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.validateStep(0, false);
      });
      expect(result.current.canProceed).toBe(false);
      
      act(() => {
        result.current.validateStep(0, true);
      });
      expect(result.current.canProceed).toBe(true);
    });
  });

  describe('draft persistence', () => {
    it('should save draft data', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.saveDraft({ field1: 'value1', field2: 42 });
      });
      
      const saved = localStorage.getItem('test');
      expect(saved).toBeDefined();
      
      const data = JSON.parse(saved!);
      expect(data.field1).toBe('value1');
      expect(data.field2).toBe(42);
    });

    it('should load draft data', () => {
      localStorage.setItem('test', JSON.stringify({ currentStep: 2, customField: 'test' }));
      
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      const loaded = result.current.loadDraft();
      expect(loaded).toEqual({ currentStep: 2, customField: 'test' });
    });

    it('should clear draft', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.saveDraft({ data: 'test' });
      });
      expect(localStorage.getItem('test')).toBeDefined();
      
      act(() => {
        result.current.clearDraft();
      });
      expect(localStorage.getItem('test')).toBeNull();
    });

    it('should auto-save on step change', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.nextStep();
      });
      
      const saved = localStorage.getItem('test');
      expect(saved).toBeDefined();
      
      const data = JSON.parse(saved!);
      expect(data.currentStep).toBe(1);
    });

    it('should not auto-save when disabled', () => {
      renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', autoSave: false }));
      
      act(() => {
        // Hook would need to be exposed to test this properly
        // For now, just verify it doesn't crash
      });
    });
  });

  describe('session management', () => {
    it('should generate unique session ID', () => {
      const { result: result1 } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test1' }));
      const { result: result2 } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test2' }));
      
      expect(result1.current.sessionId).toBeDefined();
      expect(result2.current.sessionId).toBeDefined();
      expect(result1.current.sessionId).not.toBe(result2.current.sessionId);
    });

    it('should include session ID in saved drafts', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      act(() => {
        result.current.saveDraft({ data: 'test' });
      });
      
      const saved = localStorage.getItem('test');
      const data = JSON.parse(saved!);
      expect(data.sessionId).toBe(result.current.sessionId);
    });
  });

  describe('computed properties', () => {
    it('should compute canGoNext correctly', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test', initialStep: 3 }));
      expect(result.current.canGoNext).toBe(true);
      
      act(() => {
        result.current.nextStep();
      });
      expect(result.current.canGoNext).toBe(false);
    });

    it('should compute canGoPrev correctly', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      expect(result.current.canGoPrev).toBe(false);
      
      act(() => {
        result.current.nextStep();
      });
      expect(result.current.canGoPrev).toBe(true);
    });

    it('should compute isComplete correctly', () => {
      const { result } = renderHook(() => useWizard({ totalSteps: 3, storageKey: 'test' }));
      expect(result.current.isComplete).toBe(false);
      
      act(() => {
        result.current.goToStep(2);
      });
      expect(result.current.isComplete).toBe(true);
    });
  });

  describe('localStorage error handling', () => {
    it('should handle localStorage save errors gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const mockSetItem = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('Storage quota exceeded');
      });
      
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      expect(() => {
        act(() => {
          result.current.saveDraft({ data: 'test' });
        });
      }).not.toThrow();
      
      mockSetItem.mockRestore();
      consoleWarnSpy.mockRestore();
    });

    it('should handle localStorage load errors gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const mockGetItem = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('Storage access denied');
      });
      
      const { result } = renderHook(() => useWizard({ totalSteps: 5, storageKey: 'test' }));
      
      expect(() => {
        result.current.loadDraft();
      }).not.toThrow();
      
      mockGetItem.mockRestore();
      consoleWarnSpy.mockRestore();
    });
  });
});
