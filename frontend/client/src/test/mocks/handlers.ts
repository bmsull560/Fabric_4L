/**
 * MSW (Mock Service Worker) handlers for API mocking in tests.
 * Provides consistent, deterministic responses for all API endpoints.
 */

import { http, HttpResponse, delay } from 'msw';

// Helper to generate fake IDs
const generateId = (prefix: string) => `${prefix}-${Math.random().toString(36).substr(2, 9)}`;

// Mock entity data
const mockEntities = [
  { id: 'entity-001', name: 'Cloud Migration', type: 'capability', confidence: 0.95 },
  { id: 'entity-002', name: 'Cost Reduction', type: 'usecase', confidence: 0.88 },
  { id: 'entity-003', name: 'CIO', type: 'persona', confidence: 0.92 },
  { id: 'entity-004', name: 'Revenue Growth', type: 'valuedriver', confidence: 0.85 },
];

// Mock value packs
const mockValuePacks = [
  {
    id: 'pack-001',
    name: 'Digital Transformation',
    description: 'Complete digital transformation framework',
    status: 'published',
    formulas: [{ id: 'f1', name: 'ROI Formula' }],
  },
  {
    id: 'pack-002',
    name: 'Cost Optimization',
    description: 'Cost reduction strategies and formulas',
    status: 'draft',
    formulas: [],
  },
];

// Mock user
const mockUser = {
  id: 'user-001',
  email: 'test@example.com',
  name: 'Test User',
  tenant_id: 'tenant-001',
  role: 'editor',
  tier: 'advanced',
};

export const handlers = [
  // Health check
  http.get('/api/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
    });
  }),

  // Auth - Current user
  http.get('/api/auth/me', () => {
    return HttpResponse.json(mockUser);
  }),

  // Billing - Entitlements
  http.get('/api/billing/entitlements', () => {
    return HttpResponse.json([
      { featureId: 'messages', hasAccess: true, usageLimit: 100, currentUsage: 42 },
      { featureId: 'pro_models', hasAccess: true },
      { featureId: 'advanced_mode', hasAccess: true },
      { featureId: 'api_access', hasAccess: false },
    ]);
  }),

  // Billing - Subscription
  http.get('/api/billing/subscription', () => {
    return HttpResponse.json({
      id: 'sub-test-001',
      planId: 'pro',
      status: 'active',
      currentPeriodStart: new Date().toISOString(),
      currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    });
  }),

  // Billing - Report usage
  http.post('/api/billing/report-usage', async () => {
    await delay(100);
    return HttpResponse.json({ success: true });
  }),

  // Entities - List
  http.get('/api/entities', ({ request }) => {
    const url = new URL(request.url);
    const type = url.searchParams.get('type');
    const query = url.searchParams.get('q')?.toLowerCase();
    
    let entities = [...mockEntities];
    
    if (type) {
      entities = entities.filter(e => e.type === type);
    }
    
    if (query) {
      entities = entities.filter(e => 
        e.name.toLowerCase().includes(query) ||
        e.type.toLowerCase().includes(query)
      );
    }
    
    return HttpResponse.json({
      items: entities,
      total: entities.length,
      page: 1,
      pageSize: 20,
    });
  }),

  // Entities - Get single
  http.get('/api/entities/:id', ({ params }) => {
    const entity = mockEntities.find(e => e.id === params.id);
    if (!entity) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(entity);
  }),

  // Entities - Create
  http.post('/api/entities', async ({ request }) => {
    const body = await request.json() as { name: string; type: string };
    const newEntity = {
      id: generateId('entity'),
      name: body.name,
      type: body.type,
      confidence: 0.8,
      created_at: new Date().toISOString(),
    };
    return HttpResponse.json(newEntity, { status: 201 });
  }),

  // Entities - Update
  http.patch('/api/entities/:id', async ({ params, request }) => {
    const body = await request.json();
    const entity = mockEntities.find(e => e.id === params.id);
    if (!entity) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({ ...entity, ...body, updated_at: new Date().toISOString() });
  }),

  // Entities - Delete
  http.delete('/api/entities/:id', ({ params }) => {
    const entity = mockEntities.find(e => e.id === params.id);
    if (!entity) {
      return new HttpResponse(null, { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),

  // Value Packs - List
  http.get('/api/value-packs', () => {
    return HttpResponse.json({
      items: mockValuePacks,
      total: mockValuePacks.length,
    });
  }),

  // Value Packs - Get single
  http.get('/api/value-packs/:id', ({ params }) => {
    const pack = mockValuePacks.find(p => p.id === params.id);
    if (!pack) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(pack);
  }),

  // Value Packs - Apply
  http.post('/api/value-packs/:id/apply', async ({ params }) => {
    await delay(500);
    const pack = mockValuePacks.find(p => p.id === params.id);
    if (!pack) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json({
      success: true,
      message: `Applied value pack: ${pack.name}`,
      appliedAt: new Date().toISOString(),
    });
  }),

  // Formulas - List
  http.get('/api/formulas', () => {
    return HttpResponse.json({
      items: [
        { id: 'formula-001', name: 'ROI Calculator', status: 'approved', version: 3 },
        { id: 'formula-002', name: 'TCO Analysis', status: 'draft', version: 1 },
      ],
      total: 2,
    });
  }),

  // Formulas - Create
  http.post('/api/formulas', async ({ request }) => {
    const body = await request.json() as { name: string };
    await delay(200);
    return HttpResponse.json({
      id: generateId('formula'),
      name: body.name,
      status: 'draft',
      version: 1,
      created_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  // Search - Hybrid
  http.post('/api/search/hybrid', async ({ request }) => {
    const body = await request.json() as { query: string; limit?: number };
    await delay(300);
    
    return HttpResponse.json({
      results: mockEntities
        .filter(e => e.name.toLowerCase().includes(body.query.toLowerCase()))
        .slice(0, body.limit || 10),
      total: mockEntities.length,
      query: body.query,
    });
  }),

  // Graph - Full graph
  http.get('/api/graph/full', () => {
    return HttpResponse.json({
      nodes: mockEntities.map(e => ({
        id: e.id,
        label: e.name,
        type: e.type,
        confidence: e.confidence,
      })),
      edges: [
        { source: 'entity-001', target: 'entity-002', type: 'enables' },
        { source: 'entity-002', target: 'entity-003', type: 'requires' },
      ],
    });
  }),

  // Ingestion - Jobs
  http.get('/api/ingestion/jobs', () => {
    return HttpResponse.json({
      items: [
        { id: 'job-001', status: 'completed', source_type: 'document', entities_extracted: 5 },
        { id: 'job-002', status: 'processing', source_type: 'url', progress: 45 },
      ],
      total: 2,
    });
  }),

  // Ingestion - Create job
  http.post('/api/ingestion/jobs', async ({ request }) => {
    const body = await request.json();
    await delay(100);
    return HttpResponse.json({
      id: generateId('job'),
      status: 'pending',
      ...body,
      created_at: new Date().toISOString(),
    }, { status: 202 });
  }),

  // Workflows - List
  http.get('/api/workflows', () => {
    return HttpResponse.json({
      items: [
        { id: 'wf-001', name: 'Extraction Pipeline', status: 'active', last_run: new Date().toISOString() },
        { id: 'wf-002', name: 'Validation Workflow', status: 'paused' },
      ],
    });
  }),

  // Agent - Query
  http.post('/api/agent/query', async ({ request }) => {
    const body = await request.json() as { query: string };
    await delay(2000); // Simulate LLM processing
    
    return HttpResponse.json({
      response: `Based on your query "${body.query}", I found relevant information about cloud capabilities.`,
      referenced_entities: mockEntities.slice(0, 2),
      confidence: 0.87,
    });
  }),

  // Evidence - Traces
  http.get('/api/evidence/traces', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'trace-001',
          timestamp: new Date().toISOString(),
          action: 'entity_created',
          actor: 'user-001',
          resource_id: 'entity-001',
        },
      ],
      total: 1,
    });
  }),

  // Business Cases
  http.get('/api/business-cases', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'case-001',
          title: 'Cloud Migration Initiative',
          status: 'draft',
          roi_percent: 150,
          payback_months: 18,
        },
      ],
    });
  }),

  // Accounts
  http.get('/api/accounts', () => {
    return HttpResponse.json({
      items: [
        { id: 'acc-001', name: 'Acme Corporation', industry: 'Technology' },
        { id: 'acc-002', name: 'Global Industries', industry: 'Manufacturing' },
      ],
    });
  }),
];
