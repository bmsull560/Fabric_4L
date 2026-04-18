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
        const { historyIndex, history, canUndo } = get();
        if (!canUndo || historyIndex < 0) return;

        const change = history[historyIndex];
        // TODO: Apply inverse of the change to draft state
        // This would need more sophisticated state management

        set({
          historyIndex: historyIndex - 1,
          canUndo: historyIndex > 0,
          canRedo: true,
        });
      },

      redo: () => {
        const { historyIndex, history, canRedo } = get();
        if (!canRedo || historyIndex >= history.length - 1) return;

        const newIndex = historyIndex + 1;
        const change = history[newIndex];
        // TODO: Reapply the change to draft state

        set({
          historyIndex: newIndex,
          canUndo: true,
          canRedo: newIndex < history.length - 1,
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
