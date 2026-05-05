/**
 * Ontology Store — UI state for the Ontology Editor
 *
 * Manages:
 * - Selected type in the type tree
 * - Draft changes to the ontology schema
 * - Undo/redo history
 * - Validation state
 * - Editor UI state (panels visibility, etc.)
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { OntologyType, OntologyProperty, TypeRelationship, ValidationResult } from '@/hooks/useOntology';

export interface OntologyChange {
  id: string;
  timestamp: number;
  type: 'create_type' | 'update_type' | 'delete_type' | 'add_property' | 'update_property' | 'remove_property' | 'add_relationship' | 'remove_relationship';
  description: string;
  data: unknown;
}

export interface OntologyEditorState {
  // Selection state
  selectedTypeId: string | null;
  selectedPropertyId: string | null;
  expandedTypeIds: Set<string>;

  // Draft state
  draftTypes: Map<string, OntologyType>;
  draftRelationships: Map<string, TypeRelationship>;
  hasUnsavedChanges: boolean;

  // History for undo/redo
  history: OntologyChange[];
  historyIndex: number;
  canUndo: boolean;
  canRedo: boolean;

  // Validation state
  validationResult: ValidationResult | null;
  isValidating: boolean;

  // UI state
  isPublishing: boolean;
  showRelationshipMap: boolean;
  importDialogOpen: boolean;
}

export interface OntologyEditorActions {
  // Selection actions
  selectType: (typeId: string | null) => void;
  selectProperty: (propertyId: string | null) => void;
  toggleTypeExpanded: (typeId: string) => void;
  expandAllTypes: () => void;
  collapseAllTypes: () => void;

  // Draft actions
  updateDraftType: (type: OntologyType) => void;
  addPropertyToDraft: (typeId: string, property: OntologyProperty) => void;
  updatePropertyInDraft: (typeId: string, property: OntologyProperty) => void;
  removePropertyFromDraft: (typeId: string, propertyId: string) => void;
  addRelationshipToDraft: (relationship: TypeRelationship) => void;
  removeRelationshipFromDraft: (relationshipId: string) => void;
  resetDraft: () => void;
  markSaved: () => void;

  // History actions (undo/redo)
  addChange: (change: Omit<OntologyChange, 'id' | 'timestamp'>) => void;
  undo: () => void;
  redo: () => void;
  clearHistory: () => void;

  // Validation actions
  setValidationResult: (result: ValidationResult | null) => void;
  setIsValidating: (isValidating: boolean) => void;

  // UI actions
  setIsPublishing: (isPublishing: boolean) => void;
  toggleRelationshipMap: () => void;
  setImportDialogOpen: (open: boolean) => void;

  // Initialize with loaded schema
  initializeFromSchema: (types: OntologyType[], relationships: TypeRelationship[]) => void;
}

type TypeChangeData = {
  previous?: OntologyType;
  current: OntologyType;
};

type PropertyChangeData = {
  typeId: string;
  property: OntologyProperty;
  previous?: OntologyProperty;
};

type RelationshipChangeData = {
  relationship: TypeRelationship;
};

function cloneTypes(types: Map<string, OntologyType>): Map<string, OntologyType> {
  return new Map(types);
}

function cloneRelationships(relationships: Map<string, TypeRelationship>): Map<string, TypeRelationship> {
  return new Map(relationships);
}

function upsertProperty(type: OntologyType, property: OntologyProperty): OntologyType {
  const exists = type.properties.some((candidate) => candidate.id === property.id);
  return {
    ...type,
    properties: exists
      ? type.properties.map((candidate) => candidate.id === property.id ? property : candidate)
      : [...type.properties, property],
  };
}

function removeProperty(type: OntologyType, propertyId: string): OntologyType {
  return {
    ...type,
    properties: type.properties.filter((property) => property.id !== propertyId),
  };
}

function applyChange(
  state: OntologyEditorState,
  change: OntologyChange,
  direction: 'undo' | 'redo'
): Pick<OntologyEditorState, 'draftTypes' | 'draftRelationships' | 'selectedTypeId'> {
  const draftTypes = cloneTypes(state.draftTypes);
  const draftRelationships = cloneRelationships(state.draftRelationships);
  let selectedTypeId = state.selectedTypeId;

  switch (change.type) {
    case 'create_type': {
      const { previous, current } = change.data as TypeChangeData;
      if (direction === 'undo') {
        if (previous) draftTypes.set(previous.id, previous);
        else draftTypes.delete(current.id);
        if (selectedTypeId === current.id && !previous) selectedTypeId = draftTypes.keys().next().value ?? null;
      } else {
        draftTypes.set(current.id, current);
        selectedTypeId = current.id;
      }
      break;
    }
    case 'update_type': {
      const { previous, current } = change.data as TypeChangeData;
      if (direction === 'undo') {
        if (previous) draftTypes.set(previous.id, previous);
        else draftTypes.delete(current.id);
      } else {
        draftTypes.set(current.id, current);
      }
      break;
    }
    case 'add_property': {
      const { typeId, property } = change.data as PropertyChangeData;
      const type = draftTypes.get(typeId);
      if (type) {
        draftTypes.set(typeId, direction === 'undo' ? removeProperty(type, property.id) : upsertProperty(type, property));
      }
      break;
    }
    case 'update_property': {
      const { typeId, property, previous } = change.data as PropertyChangeData;
      const type = draftTypes.get(typeId);
      if (type) {
        if (direction === 'undo') {
          draftTypes.set(typeId, previous ? upsertProperty(type, previous) : removeProperty(type, property.id));
        } else {
          draftTypes.set(typeId, upsertProperty(type, property));
        }
      }
      break;
    }
    case 'remove_property': {
      const { typeId, property } = change.data as PropertyChangeData;
      const type = draftTypes.get(typeId);
      if (type) {
        draftTypes.set(typeId, direction === 'undo' ? upsertProperty(type, property) : removeProperty(type, property.id));
      }
      break;
    }
    case 'add_relationship': {
      const { relationship } = change.data as RelationshipChangeData;
      if (direction === 'undo') draftRelationships.delete(relationship.id);
      else draftRelationships.set(relationship.id, relationship);
      break;
    }
    case 'remove_relationship': {
      const { relationship } = change.data as RelationshipChangeData;
      if (direction === 'undo') draftRelationships.set(relationship.id, relationship);
      else draftRelationships.delete(relationship.id);
      break;
    }
  }

  return { draftTypes, draftRelationships, selectedTypeId };
}

const DEFAULTS: OntologyEditorState = {
  selectedTypeId: null,
  selectedPropertyId: null,
  expandedTypeIds: new Set(),
  draftTypes: new Map(),
  draftRelationships: new Map(),
  hasUnsavedChanges: false,
  history: [],
  historyIndex: -1,
  canUndo: false,
  canRedo: false,
  validationResult: null,
  isValidating: false,
  isPublishing: false,
  showRelationshipMap: true,
  importDialogOpen: false,
};

export const useOntologyStore = create<OntologyEditorState & OntologyEditorActions>()(
  devtools(
    (set, get) => ({
      ...DEFAULTS,

      // Selection actions
      selectType: (typeId) => {
        set({ selectedTypeId: typeId, selectedPropertyId: null });
      },

      selectProperty: (propertyId) => {
        set({ selectedPropertyId: propertyId });
      },

      toggleTypeExpanded: (typeId) => {
        const { expandedTypeIds } = get();
        const newExpanded = new Set(expandedTypeIds);
        if (newExpanded.has(typeId)) {
          newExpanded.delete(typeId);
        } else {
          newExpanded.add(typeId);
        }
        set({ expandedTypeIds: newExpanded });
      },

      expandAllTypes: () => {
        const { draftTypes } = get();
        set({ expandedTypeIds: new Set(draftTypes.keys()) });
      },

      collapseAllTypes: () => {
        set({ expandedTypeIds: new Set() });
      },

      // Draft actions
      updateDraftType: (type) => {
        const { draftTypes, addChange } = get();
        const existing = draftTypes.get(type.id);

        addChange({
          type: existing ? 'update_type' : 'create_type',
          description: existing ? `Updated type "${type.name}"` : `Created type "${type.name}"`,
          data: { previous: existing, current: type },
        });

        const newDraftTypes = new Map(draftTypes);
        newDraftTypes.set(type.id, type);
        set({ draftTypes: newDraftTypes, hasUnsavedChanges: true });
      },

      addPropertyToDraft: (typeId, property) => {
        const { draftTypes, addChange } = get();
        const type = draftTypes.get(typeId);
        if (!type) return;

        addChange({
          type: 'add_property',
          description: `Added property "${property.name}" to "${type.name}"`,
          data: { typeId, property },
        });

        const updatedType = {
          ...type,
          properties: [...type.properties, property],
        };
        const newDraftTypes = new Map(draftTypes);
        newDraftTypes.set(typeId, updatedType);
        set({ draftTypes: newDraftTypes, hasUnsavedChanges: true });
      },

      updatePropertyInDraft: (typeId, property) => {
        const { draftTypes, addChange } = get();
        const type = draftTypes.get(typeId);
        if (!type) return;

        const existingProp = type.properties.find(p => p.id === property.id);

        addChange({
          type: 'update_property',
          description: `Updated property "${property.name}" in "${type.name}"`,
          data: { typeId, property, previous: existingProp },
        });

        const updatedType = {
          ...type,
          properties: type.properties.map(p => p.id === property.id ? property : p),
        };
        const newDraftTypes = new Map(draftTypes);
        newDraftTypes.set(typeId, updatedType);
        set({ draftTypes: newDraftTypes, hasUnsavedChanges: true });
      },

      removePropertyFromDraft: (typeId, propertyId) => {
        const { draftTypes, addChange } = get();
        const type = draftTypes.get(typeId);
        if (!type) return;

        const property = type.properties.find(p => p.id === propertyId);
        if (!property) return;

        addChange({
          type: 'remove_property',
          description: `Removed property "${property.name}" from "${type.name}"`,
          data: { typeId, property },
        });

        const updatedType = {
          ...type,
          properties: type.properties.filter(p => p.id !== propertyId),
        };
        const newDraftTypes = new Map(draftTypes);
        newDraftTypes.set(typeId, updatedType);
        set({ draftTypes: newDraftTypes, hasUnsavedChanges: true });
      },

      addRelationshipToDraft: (relationship) => {
        const { draftRelationships, addChange } = get();

        addChange({
          type: 'add_relationship',
          description: `Added ${relationship.relationshipType} relationship`,
          data: { relationship },
        });

        const newDraftRelationships = new Map(draftRelationships);
        newDraftRelationships.set(relationship.id, relationship);
        set({ draftRelationships: newDraftRelationships, hasUnsavedChanges: true });
      },

      removeRelationshipFromDraft: (relationshipId) => {
        const { draftRelationships, addChange, draftTypes } = get();
        const relationship = draftRelationships.get(relationshipId);
        if (!relationship) return;

        addChange({
          type: 'remove_relationship',
          description: `Removed ${relationship.relationshipType} relationship`,
          data: { relationship },
        });

        const newDraftRelationships = new Map(draftRelationships);
        newDraftRelationships.delete(relationshipId);
        set({ draftRelationships: newDraftRelationships, hasUnsavedChanges: true });
      },

      resetDraft: () => {
        set({ draftTypes: new Map(), draftRelationships: new Map(), hasUnsavedChanges: false });
      },

      markSaved: () => {
        set({ hasUnsavedChanges: false });
      },

      // History actions
      addChange: (change) => {
        const { history, historyIndex } = get();
        const newChange: OntologyChange = {
          ...change,
          id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: Date.now(),
        };

        // Remove any redo history when a new change is made
        const newHistory = history.slice(0, historyIndex + 1);
        newHistory.push(newChange);

        set({
          history: newHistory,
          historyIndex: newHistory.length - 1,
          canUndo: newHistory.length > 0,
          canRedo: false,
        });
      },

      undo: () => {
        const state = get();
        const { historyIndex, canUndo } = state;
        if (!canUndo || historyIndex < 0) return;

        const restoredDraft = applyChange(state, state.history[historyIndex], 'undo');

        set({
          ...restoredDraft,
          historyIndex: historyIndex - 1,
          canUndo: historyIndex > 0,
          canRedo: true,
          hasUnsavedChanges: true,
        });
      },

      redo: () => {
        const state = get();
        const { historyIndex, history, canRedo } = state;
        if (!canRedo || historyIndex >= history.length - 1) return;

        const newIndex = historyIndex + 1;
        const restoredDraft = applyChange(state, history[newIndex], 'redo');

        set({
          ...restoredDraft,
          historyIndex: newIndex,
          canUndo: true,
          canRedo: newIndex < history.length - 1,
          hasUnsavedChanges: true,
        });
      },

      clearHistory: () => {
        set({ history: [], historyIndex: -1, canUndo: false, canRedo: false });
      },

      // Validation actions
      setValidationResult: (result) => {
        set({ validationResult: result });
      },

      setIsValidating: (isValidating) => {
        set({ isValidating });
      },

      // UI actions
      setIsPublishing: (isPublishing) => {
        set({ isPublishing });
      },

      toggleRelationshipMap: () => {
        const { showRelationshipMap } = get();
        set({ showRelationshipMap: !showRelationshipMap });
      },

      setImportDialogOpen: (open) => {
        set({ importDialogOpen: open });
      },

      // Initialize from schema
      initializeFromSchema: (types, relationships) => {
        const draftTypes = new Map<string, OntologyType>();
        types.forEach(type => draftTypes.set(type.id, type));

        const draftRelationships = new Map<string, TypeRelationship>();
        relationships.forEach(rel => draftRelationships.set(rel.id, rel));

        // Auto-expand root types (those without parents)
        const rootTypeIds = new Set<string>();
        draftTypes.forEach((type, id) => {
          if (!type.parentTypeId) {
            rootTypeIds.add(id);
          }
        });

        set({
          draftTypes,
          draftRelationships,
          expandedTypeIds: rootTypeIds,
          selectedTypeId: types[0]?.id || null,
          hasUnsavedChanges: false,
          history: [],
          historyIndex: -1,
          canUndo: false,
          canRedo: false,
        });
      },
    }),
    { name: 'ontology-editor-store' }
  )
);

export default useOntologyStore;
