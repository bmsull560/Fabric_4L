/**
 * Value Pilot Store
 *
 * Cross-step state management for the 7-stage workflow.
 * Persists session data across browser navigation and API interactions.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  ProspectInfo,
  EnrichedEntity,
  ModelHypothesis,
  DriverTree,
  EvidenceMatch,
  ScenarioConfig,
  ScenarioVariable,
  ScenarioResult,
  ValueCase,
} from '../types';

export interface PilotState {
  // Session metadata
  sessionId: string | null;
  currentStep: number;
  startedAt: string | null;
  
  // Prospect Setup
  prospect: ProspectInfo | null;
  
  // Intelligence
  enrichedEntities: EnrichedEntity[];
  intelligenceQuery: string;
  
  // AI Model
  hypotheses: ModelHypothesis[];
  selectedHypothesisIds: string[];
  
  // Driver Tree
  selectedTreeId: string | null;
  driverTree: DriverTree | null;
  selectedNodeIds: string[];
  
  // Evidence
  evidenceMatches: EvidenceMatch[];
  verifiedEvidenceIds: string[];
  
  // Calculator
  scenario: ScenarioConfig | null;
  scenarioResult: ScenarioResult | null;
  
  // Value Case
  generatedCaseId: string | null;
  valueCase: ValueCase | null;
  
  // Step validation state
  stepValidation: Record<number, boolean>;
}

export interface PilotActions {
  // Session management
  initSession: () => void;
  clearSession: () => void;
  setCurrentStep: (step: number) => void;
  
  // Prospect Setup
  setProspect: (prospect: ProspectInfo) => void;
  updateProspect: (updates: Partial<ProspectInfo>) => void;
  
  // Intelligence
  setEnrichedEntities: (entities: EnrichedEntity[]) => void;
  addEnrichedEntity: (entity: EnrichedEntity) => void;
  setIntelligenceQuery: (query: string) => void;
  
  // AI Model
  setHypotheses: (hypotheses: ModelHypothesis[]) => void;
  selectHypothesis: (id: string) => void;
  deselectHypothesis: (id: string) => void;
  
  // Driver Tree
  setSelectedTreeId: (id: string | null) => void;
  setDriverTree: (tree: DriverTree | null) => void;
  selectNode: (id: string) => void;
  deselectNode: (id: string) => void;
  
  // Evidence
  setEvidenceMatches: (matches: EvidenceMatch[]) => void;
  verifyEvidence: (id: string) => void;
  unverifyEvidence: (id: string) => void;
  
  // Calculator
  setScenario: (scenario: ScenarioConfig) => void;
  setScenarioResult: (result: ScenarioResult) => void;
  updateVariable: (id: string, updates: Partial<ScenarioVariable>) => void;
  
  // Value Case
  setGeneratedCaseId: (id: string | null) => void;
  setValueCase: (valueCase: ValueCase | null) => void;
  updateValueCaseStatus: (status: ValueCase['status']) => void;
  
  // Validation
  validateStep: (step: number, isValid: boolean) => void;
  
  // Computed
  get canProceed(): boolean;
}

const generateSessionId = () => `pilot_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;

const initialState: Omit<PilotState, 'canProceed'> = {
  sessionId: null,
  currentStep: 0,
  startedAt: null,
  
  prospect: null,
  
  enrichedEntities: [],
  intelligenceQuery: '',
  
  hypotheses: [],
  selectedHypothesisIds: [],
  
  selectedTreeId: null,
  driverTree: null,
  selectedNodeIds: [],
  
  evidenceMatches: [],
  verifiedEvidenceIds: [],
  
  scenario: null,
  scenarioResult: null,
  
  generatedCaseId: null,
  valueCase: null,
  
  stepValidation: {},
};

export const usePilotStore = create<PilotState & PilotActions>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      // Session management
      initSession: () => set({
        ...initialState,
        sessionId: generateSessionId(),
        startedAt: new Date().toISOString(),
      }),
      
      clearSession: () => set(initialState),
      
      setCurrentStep: (step) => {
        const validStep = Math.min(6, Math.max(0, step));
        set({ currentStep: validStep });
      },
      
      // Prospect Setup
      setProspect: (prospect) => set({ prospect }),
      
      updateProspect: (updates) => set((state) => ({
        prospect: state.prospect ? { ...state.prospect, ...updates } : null,
      })),
      
      // Intelligence
      setEnrichedEntities: (entities) => set({ enrichedEntities: entities }),
      
      addEnrichedEntity: (entity) => set((state) => ({
        enrichedEntities: [...state.enrichedEntities, entity],
      })),
      
      setIntelligenceQuery: (query) => set({ intelligenceQuery: query }),
      
      // AI Model
      setHypotheses: (hypotheses) => set({ hypotheses }),
      
      selectHypothesis: (id) => set((state) => ({
        selectedHypothesisIds: state.selectedHypothesisIds.includes(id)
          ? state.selectedHypothesisIds
          : [...state.selectedHypothesisIds, id],
      })),
      
      deselectHypothesis: (id) => set((state) => ({
        selectedHypothesisIds: state.selectedHypothesisIds.filter((hid) => hid !== id),
      })),
      
      // Driver Tree
      setSelectedTreeId: (id) => set({ selectedTreeId: id }),
      
      setDriverTree: (tree) => set({ driverTree: tree }),
      
      selectNode: (id) => set((state) => ({
        selectedNodeIds: state.selectedNodeIds.includes(id)
          ? state.selectedNodeIds
          : [...state.selectedNodeIds, id],
      })),
      
      deselectNode: (id) => set((state) => ({
        selectedNodeIds: state.selectedNodeIds.filter((nid) => nid !== id),
      })),
      
      // Evidence
      setEvidenceMatches: (matches) => set({ evidenceMatches: matches }),
      
      verifyEvidence: (id) => set((state) => ({
        verifiedEvidenceIds: state.verifiedEvidenceIds.includes(id)
          ? state.verifiedEvidenceIds
          : [...state.verifiedEvidenceIds, id],
      })),
      
      unverifyEvidence: (id) => set((state) => ({
        verifiedEvidenceIds: state.verifiedEvidenceIds.filter((eid) => eid !== id),
      })),
      
      // Calculator
      setScenario: (scenario) => set({ scenario }),
      
      setScenarioResult: (result) => set({ scenarioResult: result }),
      
      updateVariable: (id, updates) => set((state) => ({
        scenario: state.scenario
          ? {
              ...state.scenario,
              variables: state.scenario.variables.map((v) =>
                v.id === id ? { ...v, ...updates } : v
              ),
            }
          : null,
      })),
      
      // Value Case
      setGeneratedCaseId: (id) => set({ generatedCaseId: id }),
      
      setValueCase: (valueCase) => set({ valueCase }),
      
      updateValueCaseStatus: (status) => set((state) => ({
        valueCase: state.valueCase ? { ...state.valueCase, status } : null,
      })),
      
      // Validation
      validateStep: (step, isValid) => set((state) => ({
        stepValidation: { ...state.stepValidation, [step]: isValid },
      })),
      
      // Computed getter - recalculates based on current state
      get canProceed() {
        const state = get();
        const currentStep = state.currentStep;
        
        // Step 0 (Prospect): requires company
        if (currentStep === 0) return !!state.prospect?.companyId;
        
        // Step 1 (Intelligence): requires at least one entity
        if (currentStep === 1) return state.enrichedEntities.length > 0;
        
        // Step 2 (AI Model): requires at least one selected hypothesis
        if (currentStep === 2) return state.selectedHypothesisIds.length > 0;
        
        // Step 3 (Driver Tree): requires tree selection
        if (currentStep === 3) return !!state.selectedTreeId;
        
        // Step 4 (Evidence): always pass (optional step)
        if (currentStep === 4) return true;
        
        // Step 5 (Calculator): requires scenario result
        if (currentStep === 5) return !!state.scenarioResult;
        
        // Step 6 (Value Case): requires generated case
        if (currentStep === 6) return !!state.generatedCaseId;
        
        return false;
      },
    }),
    {
      name: 'value-pilot-session',
      partialize: (state) => ({
        sessionId: state.sessionId,
        currentStep: state.currentStep,
        startedAt: state.startedAt,
        prospect: state.prospect,
        enrichedEntities: state.enrichedEntities,
        selectedTreeId: state.selectedTreeId,
        driverTree: state.driverTree,
        scenario: state.scenario,
        scenarioResult: state.scenarioResult,
        generatedCaseId: state.generatedCaseId,
        valueCase: state.valueCase,
      }),
    }
  )
);
