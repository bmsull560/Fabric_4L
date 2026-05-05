import { describe, expect, it, beforeEach } from 'vitest';
import useOntologyStore from './ontologyStore';
import type { OntologyType, OntologyProperty, TypeRelationship } from '@/hooks/useOntology';

function makeType(overrides: Partial<OntologyType> = {}): OntologyType {
  return {
    id: 'type-customer',
    name: 'Customer',
    description: 'Customer type',
    properties: [],
    childrenTypeIds: [],
    createdAt: '2026-01-01T00:00:00.000Z',
    updatedAt: '2026-01-01T00:00:00.000Z',
    version: 1,
    ...overrides,
  };
}

function makeProperty(overrides: Partial<OntologyProperty> = {}): OntologyProperty {
  return {
    id: 'prop-email',
    name: 'email',
    type: 'string',
    description: 'Email address',
    required: true,
    ...overrides,
  };
}

function makeRelationship(overrides: Partial<TypeRelationship> = {}): TypeRelationship {
  return {
    id: 'rel-customer-order',
    sourceTypeId: 'type-customer',
    targetTypeId: 'type-order',
    relationshipType: 'relates_to',
    cardinality: 'one_to_many',
    ...overrides,
  };
}

describe('ontologyStore undo/redo', () => {
  beforeEach(() => {
    useOntologyStore.getState().initializeFromSchema([], []);
  });

  it('undoes and redoes type creation without leaving stale selections', () => {
    const store = useOntologyStore.getState();
    const type = makeType();

    store.updateDraftType(type);
    expect(useOntologyStore.getState().draftTypes.get(type.id)).toEqual(type);

    useOntologyStore.getState().selectType(type.id);
    useOntologyStore.getState().undo();
    expect(useOntologyStore.getState().draftTypes.has(type.id)).toBe(false);
    expect(useOntologyStore.getState().selectedTypeId).toBeNull();

    useOntologyStore.getState().redo();
    expect(useOntologyStore.getState().draftTypes.get(type.id)).toEqual(type);
    expect(useOntologyStore.getState().selectedTypeId).toBe(type.id);
  });

  it('undoes and redoes property updates on the selected type draft', () => {
    const type = makeType({ properties: [makeProperty()] });
    useOntologyStore.getState().initializeFromSchema([type], []);

    const updatedProperty = makeProperty({ description: 'Primary email address', required: false });
    useOntologyStore.getState().updatePropertyInDraft(type.id, updatedProperty);
    expect(useOntologyStore.getState().draftTypes.get(type.id)?.properties[0]).toEqual(updatedProperty);

    useOntologyStore.getState().undo();
    expect(useOntologyStore.getState().draftTypes.get(type.id)?.properties[0]).toEqual(makeProperty());

    useOntologyStore.getState().redo();
    expect(useOntologyStore.getState().draftTypes.get(type.id)?.properties[0]).toEqual(updatedProperty);
  });

  it('undoes and redoes relationship removal', () => {
    const relationship = makeRelationship();
    useOntologyStore.getState().initializeFromSchema([makeType(), makeType({ id: 'type-order', name: 'Order' })], [relationship]);

    useOntologyStore.getState().removeRelationshipFromDraft(relationship.id);
    expect(useOntologyStore.getState().draftRelationships.has(relationship.id)).toBe(false);

    useOntologyStore.getState().undo();
    expect(useOntologyStore.getState().draftRelationships.get(relationship.id)).toEqual(relationship);

    useOntologyStore.getState().redo();
    expect(useOntologyStore.getState().draftRelationships.has(relationship.id)).toBe(false);
  });
});
