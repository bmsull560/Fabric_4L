/**
 * Test data factories for Playwright tests
 *
 * Provides deterministic, realistic test data that mirrors
 * production data structures without coupling to implementation.
 */

import { faker } from '@faker-js/faker';

// Use a fixed seed for deterministic test data
faker.seed(12345);

export interface TestDomain {
  url: string;
  name: string;
}

export interface TestIngestionJob {
  id: string;
  domain: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
}

export interface TestGraphNode {
  id: string;
  name: string;
  entityType: 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver';
  description: string;
}

/**
 * Generate a realistic test domain for ingestion tests
 */
export function createTestDomain(overrides?: Partial<TestDomain>): TestDomain {
  const companyName = faker.company.name();
  return {
    url: `https://${faker.internet.domainName()}`,
    name: companyName,
    ...overrides,
  };
}

/**
 * Generate test ingestion job data
 */
export function createTestIngestionJob(
  status: TestIngestionJob['status'] = 'completed',
  overrides?: Partial<TestIngestionJob>
): TestIngestionJob {
  const domain = createTestDomain();
  return {
    id: faker.string.uuid(),
    domain: domain.url,
    status,
    progress: status === 'completed' ? 100 : status === 'failed' ? 0 : faker.number.int({ min: 10, max: 90 }),
    ...overrides,
  };
}

/**
 * Generate test graph node data
 */
export function createTestGraphNode(
  entityType: TestGraphNode['entityType'] = 'Capability',
  overrides?: Partial<TestGraphNode>
): TestGraphNode {
  const typeNames: Record<TestGraphNode['entityType'], string> = {
    Capability: faker.company.buzzPhrase(),
    UseCase: `${faker.commerce.productName()} ${faker.word.verb()}ing`,
    Persona: faker.person.jobTitle(),
    ValueDriver: `${faker.number.int({ min: 10, max: 50 })}% ${faker.commerce.productAdjective()} improvement`,
  };

  return {
    id: faker.string.uuid(),
    name: typeNames[entityType],
    entityType,
    description: faker.lorem.sentence(),
    ...overrides,
  };
}

/**
 * Generate multiple test entities
 */
export function createTestGraphNodes(count: number = 5): TestGraphNode[] {
  const types: TestGraphNode['entityType'][] = ['Capability', 'UseCase', 'Persona', 'ValueDriver'];
  return Array.from({ length: count }, (_, i) =>
    createTestGraphNode(types[i % types.length])
  );
}

/**
 * Known test domains that are safe to use in tests
 * (These should be replaced with mock server responses in full E2E)
 */
export const SAFE_TEST_DOMAINS = [
  { url: 'https://example.com', name: 'Example Corp' },
  { url: 'https://testcompany.io', name: 'Test Company' },
  { url: 'https://acme.dev', name: 'Acme Development' },
] as const;

/**
 * Tier configuration for access control tests
 */
export const TIER_CONFIG = {
  standard: {
    canAccess: ['/command-center', '/value-packs', '/settings'],
    cannotAccess: ['/extraction-engine', '/graph/explorer', '/admin'],
  },
  advanced: {
    canAccess: ['/command-center', '/value-packs', '/extraction-engine', '/graph/explorer', '/value-trees'],
    cannotAccess: ['/admin'],
  },
  admin: {
    canAccess: ['/command-center', '/value-packs', '/extraction-engine', '/graph/explorer', '/value-trees', '/admin'],
    cannotAccess: [],
  },
} as const;
