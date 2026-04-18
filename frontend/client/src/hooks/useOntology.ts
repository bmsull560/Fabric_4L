import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';

// Layer key for Layer 2 Extraction API
const LAYER2: 'l2' = 'l2';

export interface OntologyType {
  id: string;
  name: string;
  description: string;
  properties: OntologyProperty[];
  parentTypeId?: string;
  childrenTypeIds?: string[];
  createdAt: string;
  updatedAt: string;
  version: number;
}

export interface OntologyProperty {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object' | 'reference';
  description?: string;
  required: boolean;
  defaultValue?: unknown;
  constraints?: PropertyConstraints;
  referenceTypeId?: string;
}

export interface PropertyConstraints {
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: string;
  enum?: string[];
}

export interface TypeRelationship {
  id: string;
  sourceTypeId: string;
  targetTypeId: string;
  relationshipType: 'depends_on' | 'extends' | 'relates_to' | 'contains';
  description?: string;
  cardinality: 'one_to_one' | 'one_to_many' | 'many_to_many';
}

export interface OntologySchema {
  types: OntologyType[];
  relationships: TypeRelationship[];
  version: string;
  publishedAt?: string;
  publishedBy?: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  typeId?: string;
  propertyId?: string;
  relationshipId?: string;
  message: string;
  code: string;
}

export interface ValidationWarning {
  typeId?: string;
  propertyId?: string;
  message: string;
  code: string;
}

// Fetch full ontology schema
export function useOntologySchema() {
  return useQuery({
    queryKey: QK.ontology.schema(),
    queryFn: async (): Promise<OntologySchema> => {
      const response = await apiClient.get(LAYER2, '/v1/ontology/schema');
      return response.data;
    },
    staleTime: STALE_TIME.reference,
  });
}

// Fetch single type with details
export function useOntologyType(typeId: string | null) {
  return useQuery({
    queryKey: QK.ontology.type(typeId || ''),
    queryFn: async (): Promise<OntologyType | null> => {
      if (!typeId) return null;
      const response = await apiClient.get(`l2`, `/v1/ontology/schema/types/${typeId}`);
      return response.data;
    },
    enabled: !!typeId,
    staleTime: STALE_TIME.detail,
  });
}

// Create new type
export function useCreateOntologyType() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (newType: Omit<OntologyType, 'id' | 'createdAt' | 'updatedAt' | 'version'>): Promise<OntologyType> => {
      const response = await apiClient.post(LAYER2, '/v1/ontology/schema/types', {
        name: newType.name,
        description: newType.description,
        parent_type_id: newType.parentTypeId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Update type
export function useUpdateOntologyType() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updatedType: OntologyType): Promise<OntologyType> => {
      const response = await apiClient.put(LAYER2, `/v1/ontology/schema/types/${updatedType.id}`, {
        name: updatedType.name,
        description: updatedType.description,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
      queryClient.invalidateQueries({ queryKey: QK.ontology.type(variables.id) });
    },
  });
}

// Delete type
export function useDeleteOntologyType() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (typeId: string): Promise<void> => {
      await apiClient.delete(LAYER2, `/v1/ontology/schema/types/${typeId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Add property to type
export function useAddOntologyProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ typeId, property }: { typeId: string; property: Omit<OntologyProperty, 'id'> }): Promise<OntologyProperty> => {
      const response = await apiClient.post(LAYER2, `/v1/ontology/schema/types/${typeId}/properties`, property);
      // Return the updated type's last property
      const updatedType = response.data as OntologyType;
      return updatedType.properties[updatedType.properties.length - 1];
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.type(variables.typeId) });
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Update property
export function useUpdateOntologyProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ typeId, property }: { typeId: string; property: OntologyProperty }): Promise<OntologyProperty> => {
      await apiClient.put(LAYER2, `/v1/ontology/schema/types/${typeId}/properties/${property.id}`, property);
      return property;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.type(variables.typeId) });
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Remove property from type
export function useRemoveOntologyProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ typeId, propertyId }: { typeId: string; propertyId: string }): Promise<void> => {
      await apiClient.delete(LAYER2, `/v1/ontology/schema/types/${typeId}/properties/${propertyId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.type(variables.typeId) });
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Add relationship between types
export function useAddTypeRelationship() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (relationship: Omit<TypeRelationship, 'id'>): Promise<TypeRelationship> => {
      const response = await apiClient.post(LAYER2, '/v1/ontology/schema/relationships', {
        source_type_id: relationship.sourceTypeId,
        target_type_id: relationship.targetTypeId,
        relationship_type: relationship.relationshipType,
        description: relationship.description,
        cardinality: relationship.cardinality,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Remove relationship
export function useRemoveTypeRelationship() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (relationshipId: string): Promise<void> => {
      await apiClient.delete(LAYER2, `/v1/ontology/schema/relationships/${relationshipId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Validate ontology schema
export function useValidateOntology() {
  return useMutation({
    mutationFn: async (schema: OntologySchema): Promise<ValidationResult> => {
      const response = await apiClient.post(LAYER2, '/v1/ontology/schema/validate', {
        types: schema.types,
        relationships: schema.relationships,
      });
      return response.data;
    },
  });
}

// Publish ontology
export function usePublishOntology() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ version, comment }: { version: string; comment?: string }): Promise<{ version: string; publishedAt: string; publishedBy: string }> => {
      const response = await apiClient.post(LAYER2, '/v1/ontology/schema/publish', {
        version,
        comment,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

// Import ontology from JSON
export function useImportOntology() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jsonData: string): Promise<OntologySchema> => {
      const response = await apiClient.post(LAYER2, '/v1/ontology/schema/import', {
        schema_json: jsonData,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.ontology.schema() });
    },
  });
}

