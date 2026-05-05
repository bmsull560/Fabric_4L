import { z } from 'zod';
import { apiClient } from './client';
import type { operations } from './generated/l3-types';

export interface ValuePackFrameworkData {
  industry_id: string;
  display_name: string;
  tier: 1 | 2 | 3;
  description: string;
  primary_value_drivers: Array<{
    id: string;
    name: string;
    description: string;
    typical_impact: string;
    measurement_approach: string;
  }>;
  core_use_cases: Array<{
    id: string;
    name: string;
    description: string;
    target_persona: string;
    business_problem: string;
  }>;
  economic_model_types: Array<{
    id: string;
    name: string;
    formula_shape: string;
    inputs: string[];
    output_unit: string;
    typical_range?: string;
  }>;
  why_it_wins: Array<{
    statement: string;
    differentiation: string;
    proof_point: string;
  }>;
  composable_model_templates: Array<{
    template_id: string;
    template_name: string;
    formula_pattern: string;
    applicable_industries: string[];
    example_calculation: string;
  }>;
  pre_wired_ontology_tags: Array<{
    tag: string;
    category: string;
    related_tags: string[];
  }>;
  metadata: {
    deal_size_range: string;
    sales_cycle_length: string;
    switching_cost: 'low' | 'medium' | 'high';
    data_richness: 'low' | 'medium' | 'high';
    feedback_loop_speed: 'slow' | 'medium' | 'fast';
  };
  completeness_score?: number;
  proof_requirements?: Array<{
    id: string;
    requirement: string;
    evidence_type: string;
  } | null>;
}

export interface OntologyMapData {
  shared_drivers: Array<{
    id: string;
    name: string;
    industries: string[];
    count: number;
  }>;
  shared_model_types: Array<{
    id: string;
    name: string;
    industries: string[];
    count: number;
  }>;
  shared_proof_patterns: Array<{
    id: string;
    requirement: string;
    industries: string[];
    count: number;
  }>;
  cross_reference_matrix: Record<string, Record<string, number>>;
}

export interface TemplateLibraryData {
  templates: ValuePackFrameworkData['composable_model_templates'];
  template_usage: Record<string, string[]>;
}

export interface ValuePackComparisonRequest {
  industry_ids: string[];
  dimensions?: string[];
}

export interface ValuePackComparisonData {
  valuepacks: ValuePackFrameworkData[];
  comparison_matrix: Record<string, Record<string, string[] | string>>;
  shared_templates: string[];
  differentiation_analysis: Record<string, string>;
}

type ListFrameworkResponse =
  operations['list_valuepacks_v1_valuepacks_get']['responses'][200]['content']['application/json'];

const SwitchingCostSchema = z.enum(['low', 'medium', 'high']);
const FeedbackSpeedSchema = z.enum(['slow', 'medium', 'fast']);

const FrameworkListItemSchema = z.object({
  industry_id: z.string(),
  display_name: z.string().optional(),
  industry_name: z.string().optional(),
  tier: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  description: z.string().default(''),
  driver_count: z.number().int().nonnegative().optional(),
  formula_count: z.number().int().nonnegative().optional(),
  updated_at: z.string().optional(),
  primary_value_drivers: z.array(z.object({
    id: z.string(),
    name: z.string(),
    description: z.string().default(''),
    typical_impact: z.string().default(''),
    measurement_approach: z.string().default(''),
  })).optional(),
  core_use_cases: z.array(z.object({
    id: z.string(),
    name: z.string(),
    description: z.string().default(''),
    target_persona: z.string().default(''),
    business_problem: z.string().default(''),
  })).optional(),
  economic_model_types: z.array(z.object({
    id: z.string(),
    name: z.string(),
    formula_shape: z.string().default(''),
    inputs: z.array(z.string()).default([]),
    output_unit: z.string().default(''),
    typical_range: z.string().optional(),
  })).optional(),
  why_it_wins: z.array(z.object({
    statement: z.string().default(''),
    differentiation: z.string().default(''),
    proof_point: z.string().default(''),
  })).optional(),
  composable_model_templates: z.array(z.object({
    template_id: z.string().optional(),
    id: z.string().optional(),
    template_name: z.string().optional(),
    name: z.string().optional(),
    formula_pattern: z.string().optional(),
    category: z.string().optional(),
    applicable_industries: z.array(z.string()).optional(),
    example_calculation: z.string().optional(),
  })).optional(),
  pre_wired_ontology_tags: z.array(z.object({
    tag: z.string(),
    category: z.string().default('general'),
    related_tags: z.array(z.string()).default([]),
  })).optional(),
  metadata: z.object({
    deal_size_range: z.string().default('Unknown'),
    sales_cycle_length: z.string().default('Unknown'),
    switching_cost: SwitchingCostSchema.default('medium'),
    data_richness: SwitchingCostSchema.default('medium'),
    feedback_loop_speed: FeedbackSpeedSchema.default('medium'),
  }).optional(),
  completeness_score: z.number().optional(),
  proof_requirements: z.array(z.object({
    id: z.string(),
    requirement: z.string(),
    evidence_type: z.string(),
  }).nullable()).optional(),
});

const FrameworkListResponseSchema = z.object({
  items: z.array(FrameworkListItemSchema),
  total: z.number().optional(),
});

const OntologyMapResponseSchema = z.union([
  z.object({
    shared_drivers: z.array(z.object({
      id: z.string(),
      name: z.string(),
      industries: z.array(z.string()).default([]),
      count: z.number().int().nonnegative().default(0),
    })),
    shared_model_types: z.array(z.object({
      id: z.string(),
      name: z.string(),
      industries: z.array(z.string()).default([]),
      count: z.number().int().nonnegative().default(0),
    })).default([]),
    shared_proof_patterns: z.array(z.object({
      id: z.string(),
      requirement: z.string(),
      industries: z.array(z.string()).default([]),
      count: z.number().int().nonnegative().default(0),
    })).default([]),
    cross_reference_matrix: z.record(z.string(), z.record(z.string(), z.number())).default({}),
  }),
  z.object({
    domains: z.array(z.string()).default([]),
    entity_types: z.array(z.string()).default([]),
    relationship_types: z.array(z.string()).default([]),
  }),
]);

const TemplateLibraryResponseSchema = z.object({
  templates: z.array(z.object({
    template_id: z.string().optional(),
    id: z.string().optional(),
    template_name: z.string().optional(),
    name: z.string().optional(),
    formula_pattern: z.string().optional(),
    category: z.string().optional(),
    applicable_industries: z.array(z.string()).optional(),
    example_calculation: z.string().optional(),
  })),
  template_usage: z.record(z.string(), z.array(z.string())).optional(),
});

const ComparisonResponseSchema = z.object({
  valuepacks: z.array(FrameworkListItemSchema),
  comparison_matrix: z.record(z.string(), z.record(z.string(), z.union([z.array(z.string()), z.string()]))),
  shared_templates: z.array(z.string()).default([]),
  differentiation_analysis: z.record(z.string(), z.string()).default({}),
});

function adaptFrameworkItem(item: z.infer<typeof FrameworkListItemSchema>): ValuePackFrameworkData {
  const displayName = item.display_name ?? item.industry_name ?? item.industry_id;
  const driverCount = item.driver_count ?? 0;
  const formulaCount = item.formula_count ?? 0;

  const defaultDrivers = Array.from({ length: driverCount }).map((_, index) => ({
    id: `${item.industry_id}-driver-${index + 1}`,
    name: `Driver ${index + 1}`,
    description: '',
    typical_impact: '',
    measurement_approach: '',
  }));

  const defaultModels = Array.from({ length: formulaCount }).map((_, index) => ({
    id: `${item.industry_id}-model-${index + 1}`,
    name: `Model ${index + 1}`,
    formula_shape: '',
    inputs: [],
    output_unit: '',
  }));

  return {
    industry_id: item.industry_id,
    display_name: displayName,
    tier: item.tier,
    description: item.description,
    primary_value_drivers: item.primary_value_drivers ?? defaultDrivers,
    core_use_cases: item.core_use_cases ?? [],
    economic_model_types: item.economic_model_types ?? defaultModels,
    why_it_wins: item.why_it_wins ?? [],
    composable_model_templates: (item.composable_model_templates ?? []).map((template, index) => ({
      template_id: template.template_id ?? template.id ?? `${item.industry_id}-template-${index + 1}`,
      template_name: template.template_name ?? template.name ?? `Template ${index + 1}`,
      formula_pattern: template.formula_pattern ?? template.category ?? '',
      applicable_industries: template.applicable_industries ?? [displayName],
      example_calculation: template.example_calculation ?? '',
    })),
    pre_wired_ontology_tags: item.pre_wired_ontology_tags ?? [],
    metadata: item.metadata ?? {
      deal_size_range: 'Unknown',
      sales_cycle_length: 'Unknown',
      switching_cost: 'medium',
      data_richness: 'medium',
      feedback_loop_speed: 'medium',
    },
    completeness_score: item.completeness_score,
    proof_requirements: item.proof_requirements,
  };
}

export async function listFrameworkValuePacks(
  tier?: number,
  search?: string
): Promise<ValuePackFrameworkData[]> {
  const params = new URLSearchParams();
  if (tier) params.set('tier', String(tier));
  if (search) params.set('search', search);

  const query = params.toString();
  const path = query.length > 0 ? `/valuepacks?${query}` : '/valuepacks';
  const response = await apiClient.get('l3', path);
  const parsed = FrameworkListResponseSchema.parse(response.data as ListFrameworkResponse);
  return parsed.items.map(adaptFrameworkItem);
}

export async function getFrameworkValuePack(industryId: string): Promise<ValuePackFrameworkData> {
  const response = await apiClient.get('l3', `/valuepacks/${industryId}`);
  const parsed = FrameworkListItemSchema.parse(response.data);
  return adaptFrameworkItem(parsed);
}

export async function getOntologyMap(): Promise<OntologyMapData> {
  const response = await apiClient.get('l3', '/valuepacks/ontology-map');
  const parsed = OntologyMapResponseSchema.parse(response.data);

  if ('shared_drivers' in parsed) {
    return parsed;
  }

  return {
    shared_drivers: parsed.domains.map((domain, index) => ({
      id: `domain-${index + 1}`,
      name: domain,
      industries: [],
      count: 0,
    })),
    shared_model_types: parsed.entity_types.map((entityType, index) => ({
      id: `entity-type-${index + 1}`,
      name: entityType,
      industries: [],
      count: 0,
    })),
    shared_proof_patterns: parsed.relationship_types.map((relationshipType, index) => ({
      id: `relationship-type-${index + 1}`,
      requirement: relationshipType,
      industries: [],
      count: 0,
    })),
    cross_reference_matrix: {},
  };
}

export async function getTemplateLibrary(): Promise<TemplateLibraryData> {
  const response = await apiClient.get('l3', '/valuepacks/composable-templates');
  const parsed = TemplateLibraryResponseSchema.parse(response.data);

  return {
    templates: parsed.templates.map((template, index) => ({
      template_id: template.template_id ?? template.id ?? `template-${index + 1}`,
      template_name: template.template_name ?? template.name ?? `Template ${index + 1}`,
      formula_pattern: template.formula_pattern ?? template.category ?? '',
      applicable_industries: template.applicable_industries ?? [],
      example_calculation: template.example_calculation ?? '',
    })),
    template_usage: parsed.template_usage ?? {},
  };
}

export async function compareFrameworkValuePacks(
  request: ValuePackComparisonRequest
): Promise<ValuePackComparisonData> {
  const response = await apiClient.post('l3', '/valuepacks/compare', request);
  const parsed = ComparisonResponseSchema.parse(response.data);

  return {
    valuepacks: parsed.valuepacks.map(adaptFrameworkItem),
    comparison_matrix: parsed.comparison_matrix,
    shared_templates: parsed.shared_templates,
    differentiation_analysis: parsed.differentiation_analysis,
  };
}
