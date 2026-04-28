/**
 * OpenAPI Schema Validator for E2E Tests
 *
 * Validates that mock response data conforms to the OpenAPI contract schemas.
 * This prevents mock drift — where test mocks silently diverge from the
 * actual backend API contract.
 *
 * Usage in tests:
 *   import { validateAgainstSchema } from '../schema-validators/openapi-validator';
 *   validateAgainstSchema('layer4-agents', '/v1/accounts/{account_id}', 'get', mockData);
 *
 * The validator loads the OpenAPI spec from contracts/openapi/ at runtime
 * and checks that the provided data matches the response schema for the
 * given path + method combination.
 */
import * as fs from 'fs';
import * as path from 'path';

// ── Types ───────────────────────────────────────────────────────────────────

type LayerName =
  | 'layer1-ingestion'
  | 'layer2-extraction'
  | 'layer3-knowledge'
  | 'layer4-agents'
  | 'layer5-ground-truth'
  | 'signals';

interface OpenApiSpec {
  paths: Record<string, Record<string, {
    responses?: Record<string, {
      content?: Record<string, {
        schema?: Record<string, unknown>;
      }>;
    }>;
  }>>;
  components?: {
    schemas?: Record<string, Record<string, unknown>>;
  };
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// ── Spec Cache ──────────────────────────────────────────────────────────────

const specCache = new Map<LayerName, OpenApiSpec>();

function loadSpec(layer: LayerName): OpenApiSpec {
  if (specCache.has(layer)) {
    return specCache.get(layer)!;
  }

  const specPath = path.resolve(
    __dirname,
    '../../../contracts/openapi',
    `${layer}.json`,
  );

  if (!fs.existsSync(specPath)) {
    throw new Error(
      `OpenAPI spec not found: ${specPath}. ` +
      `Ensure contracts/openapi/${layer}.json exists.`,
    );
  }

  const spec = JSON.parse(fs.readFileSync(specPath, 'utf-8')) as OpenApiSpec;
  specCache.set(layer, spec);
  return spec;
}

// ── Schema Resolution ───────────────────────────────────────────────────────

function resolveRef(spec: OpenApiSpec, ref: string): Record<string, unknown> | null {
  // Handle $ref like "#/components/schemas/Account"
  const parts = ref.replace('#/', '').split('/');
  let current: unknown = spec;
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return null;
    }
  }
  return current as Record<string, unknown>;
}

function getResponseSchema(
  spec: OpenApiSpec,
  apiPath: string,
  method: string,
  statusCode: string = '200',
): Record<string, unknown> | null {
  const pathDef = spec.paths[apiPath];
  if (!pathDef) return null;

  const methodDef = pathDef[method.toLowerCase()];
  if (!methodDef?.responses) return null;

  const responseDef = methodDef.responses[statusCode] || methodDef.responses['default'];
  if (!responseDef?.content) return null;

  const jsonContent = responseDef.content['application/json'];
  if (!jsonContent?.schema) return null;

  let schema = jsonContent.schema;

  // Resolve $ref if present
  if ('$ref' in schema && typeof schema['$ref'] === 'string') {
    const resolved = resolveRef(spec, schema['$ref']);
    if (resolved) schema = resolved;
  }

  return schema;
}

// ── Validation ──────────────────────────────────────────────────────────────

/**
 * Shallow validation: checks that required fields are present and
 * types roughly match. This is not a full JSON Schema validator —
 * it catches the most common mock drift issues (missing fields,
 * wrong types, array vs object confusion).
 */
function shallowValidate(
  data: unknown,
  schema: Record<string, unknown>,
  spec: OpenApiSpec,
  pathPrefix: string = '',
): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Resolve $ref at any level
  let resolvedSchema = schema;
  if ('$ref' in schema && typeof schema['$ref'] === 'string') {
    const resolved = resolveRef(spec, schema['$ref']);
    if (!resolved) {
      warnings.push(`${pathPrefix}: Could not resolve $ref: ${schema['$ref']}`);
      return { valid: true, errors, warnings };
    }
    resolvedSchema = resolved;
  }

  const schemaType = resolvedSchema['type'] as string | undefined;

  // Array check
  if (schemaType === 'array') {
    if (!Array.isArray(data)) {
      errors.push(`${pathPrefix}: Expected array, got ${typeof data}`);
      return { valid: false, errors, warnings };
    }
    // Validate first item if items schema is defined and data is non-empty
    if (resolvedSchema['items'] && (data as unknown[]).length > 0) {
      const itemResult = shallowValidate(
        (data as unknown[])[0],
        resolvedSchema['items'] as Record<string, unknown>,
        spec,
        `${pathPrefix}[0]`,
      );
      errors.push(...itemResult.errors);
      warnings.push(...itemResult.warnings);
    }
    return { valid: errors.length === 0, errors, warnings };
  }

  // Object check
  if (schemaType === 'object' || resolvedSchema['properties']) {
    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      errors.push(`${pathPrefix}: Expected object, got ${Array.isArray(data) ? 'array' : typeof data}`);
      return { valid: false, errors, warnings };
    }

    const properties = resolvedSchema['properties'] as Record<string, Record<string, unknown>> | undefined;
    const required = (resolvedSchema['required'] as string[]) || [];

    // Check required fields
    for (const field of required) {
      if (!(field in (data as Record<string, unknown>))) {
        errors.push(`${pathPrefix}.${field}: Required field missing`);
      }
    }

    // Type-check present fields
    if (properties) {
      for (const [key, propSchema] of Object.entries(properties)) {
        if (key in (data as Record<string, unknown>)) {
          const value = (data as Record<string, unknown>)[key];
          const propResult = shallowValidate(
            value,
            propSchema,
            spec,
            `${pathPrefix}.${key}`,
          );
          errors.push(...propResult.errors);
          warnings.push(...propResult.warnings);
        }
      }
    }

    return { valid: errors.length === 0, errors, warnings };
  }

  // Primitive type checks
  if (schemaType === 'string' && typeof data !== 'string' && data !== null) {
    errors.push(`${pathPrefix}: Expected string, got ${typeof data}`);
  }
  if (schemaType === 'integer' && typeof data !== 'number') {
    errors.push(`${pathPrefix}: Expected integer, got ${typeof data}`);
  }
  if (schemaType === 'number' && typeof data !== 'number') {
    errors.push(`${pathPrefix}: Expected number, got ${typeof data}`);
  }
  if (schemaType === 'boolean' && typeof data !== 'boolean') {
    errors.push(`${pathPrefix}: Expected boolean, got ${typeof data}`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ── Public API ──────────────────────────────────────────────────────────────

/**
 * Validate mock data against the OpenAPI spec for a given endpoint.
 *
 * @param layer - The backend layer name (e.g., 'layer4-agents')
 * @param apiPath - The API path template (e.g., '/v1/accounts/{account_id}')
 * @param method - HTTP method (e.g., 'get', 'post')
 * @param data - The mock response data to validate
 * @param statusCode - Expected HTTP status code (default: '200')
 * @returns ValidationResult with errors and warnings
 *
 * @example
 * ```ts
 * const result = validateAgainstSchema('layer4-agents', '/v1/accounts/{account_id}', 'get', mockAccount);
 * expect(result.valid).toBe(true);
 * ```
 */
export function validateAgainstSchema(
  layer: LayerName,
  apiPath: string,
  method: string,
  data: unknown,
  statusCode: string = '200',
): ValidationResult {
  try {
    const spec = loadSpec(layer);
    const schema = getResponseSchema(spec, apiPath, method, statusCode);

    if (!schema) {
      return {
        valid: true,
        errors: [],
        warnings: [
          `No response schema found for ${method.toUpperCase()} ${apiPath} (${statusCode}) in ${layer}. ` +
          `Schema validation skipped.`,
        ],
      };
    }

    return shallowValidate(data, schema, spec, apiPath);
  } catch (error) {
    return {
      valid: false,
      errors: [`Schema validation failed: ${(error as Error).message}`],
      warnings: [],
    };
  }
}

/**
 * List all available paths in a layer's OpenAPI spec.
 * Useful for debugging and discovering available endpoints.
 */
export function listPaths(layer: LayerName): string[] {
  const spec = loadSpec(layer);
  return Object.keys(spec.paths).sort();
}
