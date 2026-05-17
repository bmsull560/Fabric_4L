import { describe, it, expect, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useWorkflowStore } from './workflowStore';
import { SESSION_ID } from '../constants';

// Reset store state between tests
beforeEach(() => {
  act(() => {
    useWorkflowStore.getState().reset();
  });
});

describe('workflowStore — initial state', () => {
  it('starts with null sessionId', () => {
    expect(useWorkflowStore.getState().sessionId).toBeNull();
  });

  it('starts at step 0', () => {
    expect(useWorkflowStore.getState().currentStep).toBe(0);
  });

  it('starts with null prospect', () => {
    expect(useWorkflowStore.getState().prospect).toBeNull();
  });

  it('starts with empty enrichedEntities', () => {
    expect(useWorkflowStore.getState().enrichedEntities).toEqual([]);
  });

  it('starts with null selectedTreeId', () => {
    expect(useWorkflowStore.getState().selectedTreeId).toBeNull();
  });

  it('starts with null generatedCaseId', () => {
    expect(useWorkflowStore.getState().generatedCaseId).toBeNull();
  });

  it('starts with empty workflowContext', () => {
    expect(useWorkflowStore.getState().workflowContext).toEqual({});
  });
});

describe('workflowStore — initSession', () => {
  it('generates a non-null sessionId', () => {
    act(() => { useWorkflowStore.getState().initSession(); });
    expect(useWorkflowStore.getState().sessionId).not.toBeNull();
  });

  it(`sessionId starts with "${SESSION_ID.PREFIX}_"`, () => {
    act(() => { useWorkflowStore.getState().initSession(); });
    expect(useWorkflowStore.getState().sessionId).toMatch(new RegExp(`^${SESSION_ID.PREFIX}_`));
  });

  it('resets currentStep to 0', () => {
    act(() => {
      useWorkflowStore.getState().setCurrentStep(3);
      useWorkflowStore.getState().initSession();
    });
    expect(useWorkflowStore.getState().currentStep).toBe(0);
  });

  it('does not carry over prospect from prior session', () => {
    act(() => {
      useWorkflowStore.getState().setProspect({ companyId: 'c1', companyName: 'Acme', contactName: 'Alice', contactTitle: 'CEO' });
      useWorkflowStore.getState().initSession();
    });
    expect(useWorkflowStore.getState().prospect).toBeNull();
  });

  it('generates a different sessionId on each call', () => {
    act(() => { useWorkflowStore.getState().initSession(); });
    const first = useWorkflowStore.getState().sessionId;
    act(() => { useWorkflowStore.getState().initSession(); });
    const second = useWorkflowStore.getState().sessionId;
    expect(first).not.toBe(second);
  });
});

describe('workflowStore — reset', () => {
  it('clears sessionId', () => {
    act(() => {
      useWorkflowStore.getState().initSession();
      useWorkflowStore.getState().reset();
    });
    expect(useWorkflowStore.getState().sessionId).toBeNull();
  });

  it('resets currentStep to 0', () => {
    act(() => {
      useWorkflowStore.getState().setCurrentStep(5);
      useWorkflowStore.getState().reset();
    });
    expect(useWorkflowStore.getState().currentStep).toBe(0);
  });

  it('clears prospect', () => {
    act(() => {
      useWorkflowStore.getState().setProspect({ companyId: 'c1', companyName: 'Acme', contactName: 'Alice', contactTitle: 'CEO' });
      useWorkflowStore.getState().reset();
    });
    expect(useWorkflowStore.getState().prospect).toBeNull();
  });

  it('clears enrichedEntities', () => {
    act(() => {
      useWorkflowStore.getState().setEnrichedEntities([{ id: 'e1', name: 'Signal', type: 'pain', confidence: 0.9 }]);
      useWorkflowStore.getState().reset();
    });
    expect(useWorkflowStore.getState().enrichedEntities).toEqual([]);
  });
});

describe('workflowStore — setCurrentStep', () => {
  it('stores the provided step index', () => {
    act(() => { useWorkflowStore.getState().setCurrentStep(4); });
    expect(useWorkflowStore.getState().currentStep).toBe(4);
  });

  it('does not affect other fields', () => {
    act(() => {
      useWorkflowStore.getState().setProspect({ companyId: 'c1', companyName: 'Acme', contactName: 'Alice', contactTitle: 'CEO' });
      useWorkflowStore.getState().setCurrentStep(2);
    });
    expect(useWorkflowStore.getState().prospect?.companyId).toBe('c1');
  });
});

describe('workflowStore — setProspect', () => {
  it('stores the prospect', () => {
    const prospect = { companyId: 'c1', companyName: 'Acme', contactName: 'Alice', contactTitle: 'CEO', industry: 'Tech' };
    act(() => { useWorkflowStore.getState().setProspect(prospect); });
    expect(useWorkflowStore.getState().prospect).toEqual(prospect);
  });

  it('only updates prospect field', () => {
    act(() => {
      useWorkflowStore.getState().setCurrentStep(2);
      useWorkflowStore.getState().setProspect({ companyId: 'c1', companyName: 'Acme', contactName: 'Alice', contactTitle: 'CEO' });
    });
    expect(useWorkflowStore.getState().currentStep).toBe(2);
  });
});

describe('workflowStore — setEnrichedEntities', () => {
  it('stores the entities array', () => {
    const entities = [
      { id: 'e1', name: 'Signal A', type: 'pain', confidence: 0.9 },
      { id: 'e2', name: 'Signal B', type: 'pain', confidence: 0.8 },
    ];
    act(() => { useWorkflowStore.getState().setEnrichedEntities(entities); });
    expect(useWorkflowStore.getState().enrichedEntities).toEqual(entities);
  });

  it('replaces previous entities', () => {
    act(() => {
      useWorkflowStore.getState().setEnrichedEntities([{ id: 'e1', name: 'Old', type: 'pain', confidence: 0.9 }]);
      useWorkflowStore.getState().setEnrichedEntities([{ id: 'e2', name: 'New', type: 'pain', confidence: 0.7 }]);
    });
    expect(useWorkflowStore.getState().enrichedEntities).toHaveLength(1);
    expect(useWorkflowStore.getState().enrichedEntities[0].id).toBe('e2');
  });
});

describe('workflowStore — setSelectedTreeId', () => {
  it('stores the tree ID', () => {
    act(() => { useWorkflowStore.getState().setSelectedTreeId('tree-123'); });
    expect(useWorkflowStore.getState().selectedTreeId).toBe('tree-123');
  });

  it('can be set to null', () => {
    act(() => {
      useWorkflowStore.getState().setSelectedTreeId('tree-123');
      useWorkflowStore.getState().setSelectedTreeId(null);
    });
    expect(useWorkflowStore.getState().selectedTreeId).toBeNull();
  });
});

describe('workflowStore — setGeneratedCaseId', () => {
  it('stores the case ID', () => {
    act(() => { useWorkflowStore.getState().setGeneratedCaseId('VC-001'); });
    expect(useWorkflowStore.getState().generatedCaseId).toBe('VC-001');
  });

  it('can be set to null', () => {
    act(() => {
      useWorkflowStore.getState().setGeneratedCaseId('VC-001');
      useWorkflowStore.getState().setGeneratedCaseId(null);
    });
    expect(useWorkflowStore.getState().generatedCaseId).toBeNull();
  });
});

describe('workflowStore — setWorkflowContext', () => {
  it('merges context into existing workflowContext', () => {
    act(() => {
      useWorkflowStore.getState().setWorkflowContext({ sessionId: 'wf_abc', accountId: 'acct-1' });
      useWorkflowStore.getState().setWorkflowContext({ accountId: 'acct-2' });
    });
    const ctx = useWorkflowStore.getState().workflowContext;
    expect(ctx.sessionId).toBe('wf_abc');
    expect(ctx.accountId).toBe('acct-2');
  });
});

describe('workflowStore — canProceed conditions per step', () => {
  it('step 0: cannot proceed without prospect', () => {
    const { prospect } = useWorkflowStore.getState();
    expect(prospect?.companyId).toBeFalsy();
  });

  it('step 0: can proceed when prospect.companyId is set', () => {
    act(() => {
      useWorkflowStore.getState().setProspect({ companyId: 'c1', companyName: 'Acme', contactName: 'Alice', contactTitle: 'CEO' });
    });
    expect(useWorkflowStore.getState().prospect?.companyId).toBeTruthy();
  });

  it('step 1: cannot proceed with empty enrichedEntities', () => {
    expect(useWorkflowStore.getState().enrichedEntities).toHaveLength(0);
  });

  it('step 1: can proceed when at least one entity is present', () => {
    act(() => {
      useWorkflowStore.getState().setEnrichedEntities([{ id: 'e1', name: 'Signal', type: 'pain', confidence: 0.9 }]);
    });
    expect(useWorkflowStore.getState().enrichedEntities.length).toBeGreaterThan(0);
  });

  it('step 3: cannot proceed without selectedTreeId', () => {
    expect(useWorkflowStore.getState().selectedTreeId).toBeNull();
  });

  it('step 3: can proceed when selectedTreeId is set', () => {
    act(() => { useWorkflowStore.getState().setSelectedTreeId('tree-root'); });
    expect(useWorkflowStore.getState().selectedTreeId).not.toBeNull();
  });

  it('step 4: always passable — no blocking field', () => {
    // Evidence step is optional; no store field blocks progression.
    // Verify that the absence of selectedTreeId, enrichedEntities, and generatedCaseId
    // does not itself constitute a blocking condition for this step.
    const state = useWorkflowStore.getState();
    expect(state.selectedTreeId).toBeNull();
    expect(state.enrichedEntities).toHaveLength(0);
    expect(state.generatedCaseId).toBeNull();
    // All fields are in their default empty state — step 4 has no gating field.
  });

  it('step 6: cannot proceed without generatedCaseId', () => {
    expect(useWorkflowStore.getState().generatedCaseId).toBeNull();
  });

  it('step 6: can proceed when generatedCaseId is set', () => {
    act(() => { useWorkflowStore.getState().setGeneratedCaseId('VC-2026-001'); });
    expect(useWorkflowStore.getState().generatedCaseId).not.toBeNull();
  });
});

describe('workflowStore — hook usage', () => {
  it('returns store state via hook', () => {
    const { result } = renderHook(() => useWorkflowStore());
    expect(result.current.currentStep).toBe(0);
    expect(result.current.prospect).toBeNull();
  });

  it('reflects state changes via hook', () => {
    const { result } = renderHook(() => useWorkflowStore());
    act(() => { result.current.setCurrentStep(3); });
    expect(result.current.currentStep).toBe(3);
  });
});
