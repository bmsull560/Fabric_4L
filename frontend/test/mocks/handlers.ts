/**
 * MSW API Mock Handlers
 *
 * Mocks for L3 (Knowledge Graph) and L4 (Agents) API endpoints.
 * Provides predictable responses for testing hooks and components.
 */
import { http, HttpResponse, delay, type PathParams } from 'msw';

// Base API paths from environment config
// Note: L3_PREFIX must match api/client.ts LAYER_PREFIXES.l3 which is '/graph'
const API_BASE = '/api/v1';
const L2_PREFIX = '/extract';
const L3_PREFIX = '/graph';  // Layer 3 routes: /v1/graph/variables, /v1/graph/query, etc.
const L4_PREFIX = '/agents';
const L5_PREFIX = '/truths';
const L6_PREFIX = '/benchmarks';

// ===== Auth Mocks (L4) =====

export const authMocks = [
  // OIDC Login Initiation - specific error cases (MUST come before generic :tenantSlug handler)
  http.get(`${API_BASE}${L4_PREFIX}/auth/oidc/network-error/login`, async () => {
    await delay(50);
    // Simulate network failure
    return HttpResponse.error();
  }),

  http.get(`${API_BASE}${L4_PREFIX}/auth/oidc/error-tenant/login`, async () => {
    await delay(50);
    return new HttpResponse(
      JSON.stringify({ detail: 'Tenant not found' }),
      { status: 404 }
    );
  }),

  http.get(`${API_BASE}${L4_PREFIX}/auth/oidc/unauthorized/login`, async () => {
    await delay(50);
    return new HttpResponse(
      JSON.stringify({ detail: 'Unauthorized' }),
      { status: 401 }
    );
  }),

  http.get(`${API_BASE}${L4_PREFIX}/auth/oidc/server-error/login`, async () => {
    await delay(50);
    return new HttpResponse(
      JSON.stringify({ detail: 'Internal server error' }),
      { status: 500 }
    );
  }),

  // OIDC Login Initiation - default success (generic handler comes after specific ones)
  http.get(`${API_BASE}${L4_PREFIX}/auth/oidc/:tenantSlug/login`, async ({ params, request }) => {
    await delay(50);
    const tenantSlug = params.tenantSlug as string;
    const url = new URL(request.url);
    const redirectUri = url.searchParams.get('redirect_uri') || 'http://localhost:3000/login/callback';

    // Return deterministic authorization URL with state
    return HttpResponse.json({
      authorization_url: `https://idp.example.com/auth?client_id=test&redirect_uri=${encodeURIComponent(redirectUri)}&state=oidc-state-123`,
      state: 'oidc-state-123',
    });
  }),

  // OIDC Callback - Token Exchange
  http.get(`${API_BASE}${L4_PREFIX}/auth/oidc/callback`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const code = url.searchParams.get('code');
    const state = url.searchParams.get('state');

    // Simulate error cases for testing
    if (code === 'invalid-code') {
      return new HttpResponse(
        JSON.stringify({ detail: 'Invalid authorization code' }),
        { status: 400 }
      );
    }

    if (code === 'network-error') {
      return HttpResponse.error();
    }

    // Return valid TokenResponse matching schema contract
    // Uses backend-canonical role 'analyst' which normalizes to 'advanced' tier
    return HttpResponse.json({
      access_token: 'new-access-token',
      refresh_token: 'refresh-token-123',
      expires_in: 3600,
      token_type: 'Bearer',
      user_id: 'user-456',
      email: 'newuser@example.com',
      role: 'analyst',
    });
  }),
];

// ===== Workflow Mocks (L4) =====

export const workflowMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/workflows/active`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);

    const allWorkflows = [
      {
        workflow_id: 'wf-1',
        workflow_type: 'market_analysis',
        name: 'Market Analysis Workflow',
        status: 'running',
        progress_percentage: 65,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      },
      {
        workflow_id: 'wf-2',
        workflow_type: 'entity_extraction',
        name: 'Entity Extraction',
        status: 'pending',
        progress_percentage: 0,
        created_at: '2024-01-15T11:00:00Z',
        updated_at: '2024-01-15T11:00:00Z',
      },
      {
        workflow_id: 'wf-3',
        workflow_type: 'completed_job',
        name: 'Completed Analysis',
        status: 'completed',
        progress_percentage: 100,
        created_at: '2024-01-14T09:00:00Z',
        completed_at: '2024-01-14T10:30:00Z',
      },
    ];

    // Apply pagination
    const paginatedItems = allWorkflows.slice(offset, offset + limit);
    const hasMore = offset + limit < allWorkflows.length;

    return HttpResponse.json({
      items: paginatedItems,
      total: allWorkflows.length,
      limit,
      offset,
      has_more: hasMore,
    });
  }),

  http.post(`${API_BASE}${L4_PREFIX}/workflows`, async ({ request }) => {
    await delay(150);
    const body = (await request.json()) as { name?: string; workflow_type?: string };
    return HttpResponse.json({
      workflow_id: `wf-${Date.now()}`,
      workflow_instance_id: `wf-${Date.now()}`,
      name: body?.name || 'New Workflow',
      workflow_type: body?.workflow_type || 'generic',
      status: 'started',
      created_at: new Date().toISOString(),
    });
  }),

  http.delete(`${API_BASE}${L4_PREFIX}/workflows/:id`, async () => {
    await delay(100);
    return HttpResponse.json({ success: true });
  }),

  http.get(`${API_BASE}${L4_PREFIX}/workflows/:id/events`, async () => {
    // SSE endpoint - returns a stream (mocked as regular response for testing)
    return HttpResponse.json({
      type: 'workflow_update',
      payload: {
        workflow_id: 'wf-1',
        status: 'running',
        progress_percentage: 70,
      },
    });
  }),
];

// ===== Job Stream Mocks (L2) =====

export const jobStreamMocks = [
  http.get(`${API_BASE}${L2_PREFIX}/jobs/:jobId`, async ({ params }) => {
    await delay(100);
    const jobId = params.jobId as string;

    // Return specific responses for test job IDs
    if (jobId === 'job-with-logs') {
      return HttpResponse.json({
        id: jobId,
        status: 'EXTRACTING',
        progress_percent_complete: 60,
        progress_pages_found: 15,
        progress_processed_pages: 9,
        progress_logs: [
          { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Job started', status: 'OK' },
          { timestamp: '2024-01-15T10:05:00Z', level: 'INFO', message: 'Processing page 5', status: 'OK' },
          { timestamp: '2024-01-15T10:10:00Z', level: 'INFO', message: 'Extracted 10 entities', status: 'OK' },
        ],
        extracted_entities: [],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:15:00Z',
      });
    }

    if (jobId === 'job-with-entities') {
      return HttpResponse.json({
        id: jobId,
        status: 'EXTRACTING',
        progress_percent_complete: 75,
        progress_pages_found: 20,
        progress_processed_pages: 15,
        progress_logs: [],
        extracted_entities: [
          { type: 'Capability', name: 'AI Analytics' },
          { type: 'Outcome', name: 'Revenue Growth' },
          { type: 'Persona', name: 'Data Scientist' },
        ],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:15:00Z',
      });
    }

    if (jobId === 'completed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'COMPLETED',
        progress_percent_complete: 100,
        progress_pages_found: 20,
        progress_processed_pages: 20,
        progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Job completed', status: 'OK' }],
        extracted_entities: [{ type: 'Outcome', name: 'Completed Result' }],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      });
    }

    if (jobId === 'failed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'FAILED',
        progress_percent_complete: 45,
        progress_pages_found: 10,
        progress_processed_pages: 5,
        progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'ERROR', message: 'Extraction failed', status: 'ERROR' }],
        extracted_entities: [],
        configuration: { url: 'https://example.com' },
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:15:00Z',
      });
    }

    if (jobId === 'non-existent-job') {
      return new HttpResponse(JSON.stringify({ error: 'Job not found' }), { status: 404 });
    }

    // Default response for any job ID
    return HttpResponse.json({
      id: jobId,
      status: 'EXTRACTING',
      progress_percent_complete: 45,
      progress_pages_found: 10,
      progress_processed_pages: 5,
      progress_logs: [
        { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Job started', status: 'OK' },
        { timestamp: '2024-01-15T10:05:00Z', level: 'INFO', message: 'Crawling domain', status: 'OK' },
        { timestamp: '2024-01-15T10:10:00Z', level: 'INFO', message: 'Extracting entities', status: 'OK' },
      ],
      extracted_entities: [
        { type: 'Outcome', name: 'Revenue Growth' },
        { type: 'Capability', name: 'Data Analytics' },
      ],
      configuration: { url: 'https://example.com' },
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:15:00Z',
    });
  }),

  // Polling endpoint - returns same data as single job endpoint
  http.get(`${API_BASE}${L2_PREFIX}/jobs/:jobId/poll`, async ({ params }) => {
    await delay(100);
    const jobId = params.jobId as string;

    // Return consistent status for completed/failed jobs
    if (jobId === 'completed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'COMPLETED',
        progress_percent_complete: 100,
        progress_logs: [],
        extracted_entities: [],
      });
    }
    if (jobId === 'failed-job') {
      return HttpResponse.json({
        id: jobId,
        status: 'FAILED',
        progress_percent_complete: 45,
        progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'ERROR', message: 'Extraction failed' }],
        extracted_entities: [],
      });
    }

    return HttpResponse.json({
      id: jobId,
      status: 'EXTRACTING',
      progress_percent_complete: 50,
      progress_pages_found: 12,
      progress_processed_pages: 6,
      progress_logs: [
        { timestamp: '2024-01-15T10:15:00Z', level: 'INFO', message: 'Processing page 6', status: 'OK' },
      ],
      extracted_entities: [{ type: 'Outcome', name: 'Cost Reduction' }],
      configuration: { url: 'https://example.com' },
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:15:00Z',
    });
  }),

  http.get(`${API_BASE}${L2_PREFIX}/jobs/:jobId/events`, async () => {
    // SSE endpoint for job streaming
    return HttpResponse.json({
      type: 'progress',
      data: 50,
    });
  }),
];

// ===== Graph Query Mocks (L3) =====

export const graphMocks = [
  // Canonical GraphRAG endpoint (preferred)
  http.post(`${API_BASE}${L3_PREFIX}/query/graph`, async () => {
    await delay(150);
    return HttpResponse.json({
      query: 'test query',
      entities: [
        {
          id: 'ent-1',
          name: 'Test Entity',
          entity_type: 'capability',
          confidence_score: 0.95,
          description: 'A test entity',
        },
      ],
      relationships: [
        { source: 'ent-1', target: 'ent-2', type: 'RELATED_TO', confidence: 0.9 },
      ],
      context_graph: {
        nodes: [
          { id: 'ent-1', name: 'Test Entity', entity_type: 'capability', confidence_score: 0.95 },
          { id: 'ent-2', name: 'Related Entity', entity_type: 'usecase', confidence_score: 0.88 },
        ],
        relationships: [{ source: 'ent-1', target: 'ent-2', type: 'RELATED_TO' }],
      },
      confidence_score: 0.92,
      processing_time_ms: 120,
    });
  }),

  // Legacy alias for backward compatibility - redirects to same handler
  http.post(`${API_BASE}/graphrag`, async () => {
    await delay(150);
    return HttpResponse.json({
      query: 'test query (legacy alias)',
      entities: [
        {
          id: 'ent-1',
          name: 'Test Entity',
          entity_type: 'capability',
          confidence_score: 0.95,
          description: 'A test entity',
        },
      ],
      relationships: [
        { source: 'ent-1', target: 'ent-2', type: 'RELATED_TO', confidence: 0.9 },
      ],
      context_graph: {
        nodes: [
          { id: 'ent-1', name: 'Test Entity', entity_type: 'capability', confidence_score: 0.95 },
          { id: 'ent-2', name: 'Related Entity', entity_type: 'usecase', confidence_score: 0.88 },
        ],
        relationships: [{ source: 'ent-1', target: 'ent-2', type: 'RELATED_TO' }],
      },
      confidence_score: 0.92,
      processing_time_ms: 120,
      _meta: { note: 'Legacy /v1/graphrag endpoint - use /v1/query/graph for new code' },
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/entity/:entityId/context`, async ({ params, request }) => {
    await delay(100);
    const entityId = decodeURIComponent(params.entityId as string);
    const url = new URL(request.url);
    const hops = url.searchParams.get('hops') || '2';

    return HttpResponse.json({
      entity_id: entityId,
      center: {
        id: entityId,
        name: 'Center Entity',
        entity_type: 'capability',
        confidence_score: 0.95,
      },
      neighbors: [
        {
          id: 'neighbor-1',
          name: 'Neighbor One',
          entity_type: 'usecase',
          confidence_score: 0.88,
        },
        {
          id: 'neighbor-2',
          name: 'Neighbor Two',
          entity_type: 'persona',
          confidence_score: 0.82,
        },
      ],
      relationships: [
        { source: entityId, target: 'neighbor-1', type: 'ENABLES' },
        { source: 'neighbor-2', target: entityId, type: 'USES' },
      ],
      entity_count: 3,
      relationship_count: 2,
      hops: parseInt(hops, 10),
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/entity/traverse`, async () => {
    await delay(150);
    return HttpResponse.json({
      start_entity_id: 'ent-1',
      direction: 'both',
      paths: [
        {
          nodes: [
            { id: 'ent-1', name: 'Start', entity_type: 'capability', confidence_score: 0.95 },
            { id: 'ent-2', name: 'End', entity_type: 'outcome', confidence_score: 0.92 },
          ],
          relationships: [{ source: 'ent-1', target: 'ent-2', type: 'DRIVES' }],
          value_score: 0.88,
        },
      ],
      path_count: 1,
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/search/hybrid`, async () => {
    await delay(100);
    return HttpResponse.json({
      results: [
        { id: 'ent-1', name: 'Entity One', entity_type: 'capability', confidence_score: 0.95 },
        { id: 'ent-2', name: 'Entity Two', entity_type: 'usecase', confidence_score: 0.88 },
        { id: 'ent-3', name: 'Entity Three', entity_type: 'persona', confidence_score: 0.82 },
      ],
      total: 3,
    });
  }),

  // Coherent subgraph endpoint (replaces sampling approach)
  http.get(`${API_BASE}${L3_PREFIX}/subgraph`, async ({ request }) => {
    await delay(150);
    const url = new URL(request.url);
    const query = url.searchParams.get('query');
    const centerId = url.searchParams.get('center_entity_id');
    const depth = parseInt(url.searchParams.get('depth') || '2', 10);
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);

    // Mock coherent subgraph with nodes AND edges (matching GraphNodeSchema)
    const nodes = [
      { id: 'ent-1', name: 'AI Processing', entity_type: 'Capability', confidence_score: 0.95 },
      { id: 'ent-2', name: 'Data Pipeline', entity_type: 'Capability', confidence_score: 0.88 },
      { id: 'ent-3', name: 'Customer Analytics', entity_type: 'UseCase', confidence_score: 0.92 },
      { id: 'ent-4', name: 'Data Scientist', entity_type: 'Persona', confidence_score: 0.85 },
    ];

    const edges = [
      { source: 'ent-1', target: 'ent-2', type: 'ENABLES', properties: {} },
      { source: 'ent-2', target: 'ent-3', type: 'ENABLES', properties: {} },
      { source: 'ent-3', target: 'ent-4', type: 'USED_BY', properties: {} },
      { source: 'ent-1', target: 'ent-3', type: 'SUPPORTS', properties: {} },
    ];

    return HttpResponse.json({
      root_entity_id: centerId || '',
      nodes: nodes.slice(0, limit),
      edges: edges,
      depth: depth,
      stats: {
        total_nodes: nodes.length,
        total_edges: edges.length,
        density: 0.33,
      },
    });
  }),
];

// ===== Benchmark Mocks (L3) =====

export const benchmarkMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/benchmarks`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');

    const benchmarks = [
      {
        id: 'bench-1',
        benchmark_id: 'bench-1',
        name: 'Industry Average ROI',
        industry: industry || 'Software',
        vertical: 'SaaS',
        value_range: '2.5x - 4.0x',
        confidence: 'High',
        source: 'Industry Research',
        year: 2024,
        status: 'active',
        tags: ['roi', 'saas'],
        usage_count: 15,
      },
      {
        id: 'bench-2',
        benchmark_id: 'bench-2',
        name: 'Implementation Timeline',
        industry: industry || 'Software',
        vertical: 'Enterprise',
        value_range: '3-6 months',
        confidence: 'Medium',
        source: 'Survey Data',
        year: 2024,
        status: 'active',
        tags: ['timeline'],
        usage_count: 8,
      },
    ];

    return HttpResponse.json(benchmarks);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/benchmarks/policies`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'policy-1',
        policy_type: 'threshold',
        name: 'Minimum Confidence Threshold',
        description: 'Minimum confidence level for benchmark usage',
        value: '0.7',
        is_enabled: true,
        scope: 'tenant',
      },
      {
        id: 'policy-2',
        policy_type: 'cadence',
        name: 'Update Cadence',
        description: 'How often benchmarks are refreshed',
        value: 'monthly',
        is_enabled: true,
        scope: 'pack',
      },
    ]);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/benchmarks/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      benchmark_id: id,
      name: 'Detailed Benchmark',
      industry: 'Software',
      value_range: '2.5x - 4.0x',
      confidence: 'High',
      source: 'Industry Research',
      year: 2024,
      status: 'active',
      tags: ['detailed'],
      usage_count: 10,
    });
  }),

  http.put(`${API_BASE}${L3_PREFIX}/benchmarks/policies/:id`, async ({ params, request }) => {
    await delay(100);
    const id = params.id as string;
    const body = (await request.json()) as { value?: string; is_enabled?: boolean };
    return HttpResponse.json({
      id,
      policy_type: 'threshold',
      name: 'Updated Policy',
      description: 'Updated description',
      value: body?.value || '0.8',
      is_enabled: body?.is_enabled ?? true,
      scope: 'tenant',
    });
  }),
];

// ===== Formula Mocks (L3) =====

export const formulaMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/formulas/approvals/pending`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'approval-1',
        formula_id: 'formula-2',
        formula_name: 'Payback Period',
        submitted_by: 'user@example.com',
        submitted_at: '2024-01-10T09:00:00Z',
        change_summary: 'Updated calculation method',
        previous_version: '1.0.0',
        status: 'pending',
      },
    ]);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/formulas`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const statusFilter = url.searchParams.get('status');

    let formulas = [
      {
        id: 'formula-1',
        formula_id: 'formula-1',
        name: 'ROI Calculation',
        version: '1.0.0',
        status: 'active',
        owner: 'user@example.com',
        updated_at: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        used_in_count: 5,
        governance_score: 0.92,
        expression: 'revenue / cost',
        variables: ['revenue', 'cost'],
      },
      {
        id: 'formula-2',
        formula_id: 'formula-2',
        name: 'Payback Period',
        version: '2.0.0',
        status: 'draft',
        owner: 'user@example.com',
        updated_at: '2024-01-10T09:00:00Z',
        created_at: '2024-01-05T00:00:00Z',
        used_in_count: 2,
        governance_score: 0.75,
        expression: 'investment / monthly_savings',
        variables: ['investment', 'monthly_savings'],
      },
    ];

    // Apply status filter if provided
    if (statusFilter) {
      formulas = formulas.filter(f => f.status === statusFilter);
    }

    return HttpResponse.json(formulas);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/formulas/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      formula_id: id,
      name: 'Detailed Formula',
      version: '1.0.0',
      status: 'active',
      owner: 'user@example.com',
      updated_at: '2024-01-15T10:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
      used_in_count: 10,
      governance_score: 0.95,
      expression: 'a + b',
      variables: ['a', 'b'],
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/formulas/:id/approve`, async ({ params }) => {
    await delay(150);
    return HttpResponse.json({
      formula_id: params.id,
      status: 'approved',
      approved_at: new Date().toISOString(),
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/formulas/:id/submit`, async ({ params }) => {
    await delay(150);
    return HttpResponse.json({
      formula_id: params.id,
      status: 'pending_approval',
      submitted_at: new Date().toISOString(),
    });
  }),

  // Create new formula
  http.post(`${API_BASE}${L3_PREFIX}/formulas`, async ({ request }) => {
    await delay(150);
    const body = (await request.json()) as { name?: string; description?: string; expression?: string };
    const id = `formula-${Date.now()}`;
    return HttpResponse.json({
      id,
      formula_id: id,
      name: body?.name || 'New Formula',
      description: body?.description || '',
      expression: body?.expression || '',
      version: '1.0.0',
      status: 'draft',
      owner: 'user@example.com',
      updated_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      used_in_count: 0,
      governance_score: 1.0,
      variables: [],
    }, { status: 201 });
  }),

  // Update formula
  http.patch(`${API_BASE}${L3_PREFIX}/formulas/:id`, async ({ params, request }) => {
    await delay(150);
    const id = params.id as string;
    const body = (await request.json()) as { name?: string; description?: string; expression?: string };
    return HttpResponse.json({
      id,
      formula_id: id,
      name: body?.name || 'Updated Formula',
      description: body?.description || '',
      expression: body?.expression || '',
      version: '1.0.1',
      status: 'draft',
      owner: 'user@example.com',
      updated_at: new Date().toISOString(),
      created_at: '2024-01-01T00:00:00Z',
      used_in_count: 5,
      governance_score: 0.95,
      variables: [],
    });
  }),

  // Delete formula
  http.delete(`${API_BASE}${L3_PREFIX}/formulas/:id`, async ({ params }) => {
    await delay(100);
    return HttpResponse.json({
      formula_id: params.id,
      deleted: true,
      deleted_at: new Date().toISOString(),
    });
  }),

  // Evaluate formula
  http.post(`${API_BASE}${L3_PREFIX}/formulas/evaluate`, async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as { inputs?: Array<{ name: string; value: number }>; expression?: string };
    const inputs = body?.inputs || [];
    const result = inputs.reduce((sum, input) => sum + (input.value || 0), 0);

    return HttpResponse.json({
      result,
      unit: 'USD',
      confidence: 0.92,
      calculation_steps: inputs.map((input, idx) => ({
        step: idx + 1,
        operation: `Added ${input.name}`,
        result: String(input.value),
      })),
      formula_used: body?.expression || 'evaluated_formula',
    });
  }),
];

// ===== Variable Mocks (L3) =====

export const variableMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/variables`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const type = url.searchParams.get('type');
    const status = url.searchParams.get('status');
    const source = url.searchParams.get('source');
    const search = url.searchParams.get('search')?.toLowerCase();

    let variables = [
      {
        id: 'var-1',
        variable_id: 'var-1',
        name: 'monthly_revenue',
        display_name: 'Monthly Revenue',
        type: 'currency',
        unit: 'USD',
        source: 'CRM',
        binding: 'salesforce.revenue',
        binding_path: 'opportunities.amount',
        default_value: '0',
        used_in_count: 5,
        validation_status: 'validated',
        tags: ['financial', 'revenue'],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
        version: '1.0.0',
      },
      {
        id: 'var-2',
        variable_id: 'var-2',
        name: 'employee_count',
        display_name: 'Employee Count',
        type: 'integer',
        unit: 'count',
        source: 'ERP',
        binding: 'workday.headcount',
        used_in_count: 3,
        validation_status: 'pending',
        tags: ['hr'],
        created_at: '2024-01-05T00:00:00Z',
        updated_at: '2024-01-10T09:00:00Z',
        version: '1.0.0',
      },
    ];

    // Apply filters if provided
    if (status) {
      variables = variables.filter(v => v.validation_status === status);
    }
    if (source) {
      variables = variables.filter(v => v.source === source);
    }
    if (type) {
      variables = variables.filter(v => v.type === type);
    }
    if (search) {
      variables = variables.filter(
        v =>
          v.name.toLowerCase().includes(search) ||
          v.display_name.toLowerCase().includes(search)
      );
    }

    return HttpResponse.json(variables);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/variables/stats`, async () => {
    await delay(100);
    return HttpResponse.json({
      total: 50,
      validated: 40,
      pending: 8,
      failed: 2,
      manual_sources: 15,
      avg_usage: 4.5,
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/variables/bindings`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'binding-1',
        name: 'Salesforce CRM',
        source_type: 'CRM',
        connection_string: 'salesforce://production',
        status: 'connected',
        last_sync: '2024-01-15T10:00:00Z',
        variables_bound: 10,
      },
      {
        id: 'binding-2',
        name: 'Workday HR',
        source_type: 'ERP',
        status: 'disconnected',
        variables_bound: 5,
        error_message: 'Authentication expired',
      },
    ]);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/variables/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      variable_id: id,
      name: 'detailed_variable',
      display_name: 'Detailed Variable',
      type: 'float',
      unit: 'percentage',
      source: 'Database',
      binding: 'custom.db',
      binding_path: 'metrics.conversion_rate',
      default_value: '0.0',
      used_in_count: 10,
      validation_status: 'validated',
      tags: ['detailed'],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      version: '1.0.0',
    });
  }),

  http.post(`${API_BASE}${L3_PREFIX}/variables/:id/validate`, async ({ params }) => {
    await delay(150);
    return HttpResponse.json({
      variable_id: params.id,
      validation_status: 'validated',
      validated_at: new Date().toISOString(),
    });
  }),
];

// ===== Provenance Mocks (L3) =====

export const provenanceMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/provenance/:entityId`, async ({ params, request }) => {
    await delay(100);
    const entityId = decodeURIComponent(params.entityId as string);
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'json';

    return HttpResponse.json({
      entity_id: entityId,
      entity_type: 'business_case',
      entity_name: 'Test Business Case',
      source: 'extraction',
      extraction_job_id: 'job-123',
      confidence_score: 0.95,
      created_at: '2024-01-15T10:00:00Z',
      format,
      steps: [
        {
          step: 1,
          label: 'Entity Extraction',
          detail: 'Extracted from source document',
          timestamp: '2024-01-15T10:00:00Z',
          agent: 'extraction_agent',
        },
        {
          step: 2,
          label: 'Formula Application',
          detail: 'Applied ROI calculation formula',
          timestamp: '2024-01-15T10:05:00Z',
          agent: 'formula_agent',
        },
        {
          step: 3,
          label: 'Value Calculation',
          detail: 'Computed total value: $1.2M',
          timestamp: '2024-01-15T10:10:00Z',
          agent: 'calculation_agent',
        },
      ],
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/audit/logs`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const source = url.searchParams.get('source') || 'all';

    return HttpResponse.json({
      entries: [
        {
          id: 'audit-1',
          timestamp: '2024-01-15T10:00:00Z',
          source: source === 'all' ? 'provenance' : (source as 'provenance' | 'access'),
          event_type: 'create',
          entity_id: 'entity-1',
          entity_type: 'business_case',
          action: 'create',
          agent: 'user@example.com',
          details: {},
        },
        {
          id: 'audit-2',
          timestamp: '2024-01-15T10:05:00Z',
          source: source === 'all' ? 'provenance' : (source as 'provenance' | 'access'),
          event_type: 'update',
          entity_id: 'entity-1',
          entity_type: 'business_case',
          action: 'update_value',
          agent: 'formula_agent',
          details: { field: 'total_value' },
        },
      ],
      total: 2,
      page: 1,
      per_page: 20,
    });
  }),
];

// ===== Business Case Mocks (L4) =====

export const businessCaseMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/analysis/cases/:caseId`, async ({ params }) => {
    await delay(100);
    const caseId = params.caseId as string;
    return HttpResponse.json({
      case_id: caseId,
      title: 'Test Business Case',
      summary: 'This is a test business case with comprehensive analysis.',
      total_value: 1200000,
      implementation_cost: 300000,
      roi_ratio: 4.0,
      payback_months: 12,
      confidence_score: 0.92,
      recommendations: [
        'Implement solution within Q2',
        'Focus on high-value customer segments',
        'Monitor metrics monthly',
      ],
      status: 'completed',
      created_at: '2024-01-15T10:00:00Z',
      page_count: 15,
      file_size_bytes: 102400,
      document_url: 'https://example.com/docs/case.pdf',
    });
  }),

  http.get(`${API_BASE}${L4_PREFIX}/analysis/cases/:caseId/export`, async ({ params, request }) => {
    await delay(200);
    const caseId = params.caseId as string;
    const url = new URL(request.url);
    const format = url.searchParams.get('format') || 'pdf';

    return HttpResponse.json({
      case_id: caseId,
      format,
      document_url: `https://example.com/downloads/${caseId}.${format}`,
      download_ready: true,
    });
  }),
];

// ===== Value Tree Mocks (L3) =====

interface MockValueTreeNode {
  id: string;
  label: string;
  type: string;
  layer: number;
  confidence: number;
  properties: Record<string, unknown>;
}

interface MockValueTreeEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

function generateMockValueTreeNodes(rootId: string): MockValueTreeNode[] {
  return [
    {
      id: rootId,
      label: 'Root Value Driver',
      type: 'ValueDriver',
      layer: 1,
      confidence: 0.95,
      properties: { priority: 'high' },
    },
    {
      id: `${rootId}-child-1`,
      label: 'Customer Outcome',
      type: 'Persona',
      layer: 2,
      confidence: 0.88,
      properties: {},
    },
    {
      id: `${rootId}-child-2`,
      label: 'Use Case',
      type: 'UseCase',
      layer: 2,
      confidence: 0.92,
      properties: {},
    },
    {
      id: `${rootId}-grandchild-1`,
      label: 'AI Analytics',
      type: 'Capability',
      layer: 3,
      confidence: 0.85,
      properties: {},
    },
  ];
}

function generateMockValueTreeEdges(rootId: string): MockValueTreeEdge[] {
  return [
    { source: rootId, target: `${rootId}-child-1`, type: 'DRIVES', weight: 0.9 },
    { source: rootId, target: `${rootId}-child-2`, type: 'ENABLES', weight: 0.85 },
    { source: `${rootId}-child-2`, target: `${rootId}-grandchild-1`, type: 'REQUIRES', weight: 0.8 },
  ];
}

function buildLayerStats(nodes: MockValueTreeNode[]): Record<string, number> {
  return nodes.reduce((acc, node) => {
    const layer = String(node.layer);
    acc[layer] = (acc[layer] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
}

export const valueTreeMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/value-trees/:entityId`, async ({ params, request }) => {
    await delay(150);
    const entityId = decodeURIComponent(params.entityId as string);
    const url = new URL(request.url);
    const direction = url.searchParams.get('direction') || 'upward';
    const maxDepth = parseInt(url.searchParams.get('max_depth') || '4', 10);

    const nodes = generateMockValueTreeNodes(entityId);
    const edges = generateMockValueTreeEdges(entityId);

    return HttpResponse.json({
      root_entity_id: entityId,
      direction,
      nodes,
      edges,
      paths: [
        { length: 2, nodes: [entityId, `${entityId}-child-1`] },
        { length: 3, nodes: [entityId, `${entityId}-child-2`, `${entityId}-grandchild-1`] },
      ],
      stats: {
        total_nodes: nodes.length,
        total_edges: edges.length,
        by_layer: buildLayerStats(nodes),
        max_depth: maxDepth,
      },
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/value-trees/:entityId/paths`, async ({ params, request }) => {
    await delay(100);
    const entityId = decodeURIComponent(params.entityId as string);

    return HttpResponse.json([
      {
        nodes: [
          { id: entityId, name: 'Root Entity', type: 'ValueDriver' },
          { id: 'child-1', name: 'Customer Persona', type: 'Persona' },
        ],
        length: 2,
      },
      {
        nodes: [
          { id: entityId, name: 'Root Entity', type: 'ValueDriver' },
          { id: 'child-2', name: 'Primary Use Case', type: 'UseCase' },
          { id: 'grandchild-1', name: 'AI Capability', type: 'Capability' },
        ],
        length: 3,
      },
    ]);
  }),
];

// ===== Value Pack Mocks (L3) =====

export const valuePackMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/packs`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');
    const status = url.searchParams.get('status');
    const scope = url.searchParams.get('scope');
    const category = url.searchParams.get('category');
    const search = url.searchParams.get('search');

    let packs = [
      {
        id: 'pack-1',
        pack_id: 'enterprise-security-roi',
        name: 'Enterprise Security ROI',
        industry: 'SaaS / B2B',
        description: 'Comprehensive security ROI calculations for enterprise customers',
        driver_count: 5,
        formula_count: 12,
        benchmark_count: 8,
        workflow_count: 3,
        status: 'active',
        scope: 'global' as const,
        category: 'Security',
        updated_at: '2024-01-15T10:00:00Z',
        created_at: '2024-01-10T08:00:00Z',
        version: '1.2.0',
        owner: 'security-team',
        created_by: 'security-team',
      },
      {
        id: 'pack-2',
        pack_id: 'churn-reduction',
        name: 'Customer Churn Reduction',
        industry: 'SaaS / B2B',
        description: 'Analyze and reduce customer churn with predictive models',
        driver_count: 3,
        formula_count: 8,
        benchmark_count: 5,
        workflow_count: 2,
        status: 'published',
        scope: 'global' as const,
        category: 'Analytics',
        updated_at: '2024-01-14T15:30:00Z',
        created_at: '2024-01-12T09:00:00Z',
        version: '1.0.0',
        owner: 'customer-success',
        created_by: 'customer-success',
      },
      {
        id: 'pack-3',
        pack_id: 'healthcare-compliance',
        name: 'Healthcare Compliance',
        industry: 'Healthcare',
        description: 'HIPAA compliance and risk assessment tools',
        driver_count: 4,
        formula_count: 6,
        benchmark_count: 10,
        workflow_count: 4,
        status: 'draft',
        scope: 'tenant' as const,
        category: 'Compliance',
        updated_at: '2024-01-13T11:00:00Z',
        created_at: '2024-01-13T10:00:00Z',
        version: '0.9.0',
        owner: 'compliance-team',
        created_by: 'compliance-team',
      },
      {
        id: 'pack-4',
        pack_id: 'fintech-metrics',
        name: 'Fintech Metrics Suite',
        industry: 'Financial Services',
        description: 'Regulatory and growth metrics for fintech companies',
        driver_count: 6,
        formula_count: 15,
        benchmark_count: 12,
        workflow_count: 5,
        status: 'archived',
        scope: 'global' as const,
        category: 'Finance',
        updated_at: '2023-12-01T09:00:00Z',
        created_at: '2023-11-15T08:00:00Z',
        version: '0.5.0',
        owner: 'finance-team',
        created_by: 'finance-team',
      },
    ];

    // Apply filters (matching backend behavior)
    if (industry && industry !== 'all') {
      packs = packs.filter(p => p.industry.toLowerCase().includes(industry.toLowerCase()));
    }
    if (status && status !== 'all') {
      packs = packs.filter(p => p.status === status);
    }
    if (scope && scope !== 'all') {
      packs = packs.filter(p => p.scope === scope);
    }
    if (category && category !== 'all') {
      packs = packs.filter(p => p.category?.toLowerCase() === category.toLowerCase());
    }
    if (search) {
      const searchLower = search.toLowerCase();
      packs = packs.filter(p =>
        p.name.toLowerCase().includes(searchLower) ||
        p.description?.toLowerCase().includes(searchLower)
      );
    }

    return HttpResponse.json(packs);
  }),

  http.get(`${API_BASE}${L3_PREFIX}/packs/:packId`, async ({ params }) => {
    await delay(50);
    const packId = params.packId as string;
    const allPacks: Record<string, object> = {
      'enterprise-security-roi': {
        id: 'pack-1', pack_id: 'enterprise-security-roi', name: 'Enterprise Security ROI',
        industry: 'SaaS / B2B', description: 'Comprehensive security ROI calculations for enterprise customers',
        driver_count: 5, formula_count: 12, benchmark_count: 8, workflow_count: 3,
        status: 'active', scope: 'global', category: 'Security', updated_at: '2024-01-15T10:00:00Z', version: '1.2.0',
      },
      'churn-reduction': {
        id: 'pack-2', pack_id: 'churn-reduction', name: 'Customer Churn Reduction',
        industry: 'SaaS / B2B', description: 'Analyze and reduce customer churn with predictive models',
        driver_count: 3, formula_count: 8, benchmark_count: 5, workflow_count: 2,
        status: 'published', scope: 'global', category: 'Analytics', updated_at: '2024-01-14T15:30:00Z', version: '1.0.0',
      },
      'healthcare-compliance': {
        id: 'pack-3', pack_id: 'healthcare-compliance', name: 'Healthcare Compliance',
        industry: 'Healthcare', description: 'HIPAA compliance and risk assessment tools',
        driver_count: 4, formula_count: 6, benchmark_count: 10, workflow_count: 4,
        status: 'draft', scope: 'tenant', category: 'Compliance', updated_at: '2024-01-13T11:00:00Z', version: '0.9.0',
      },
      'fintech-metrics': {
        id: 'pack-4', pack_id: 'fintech-metrics', name: 'Fintech Metrics Suite',
        industry: 'Financial Services', description: 'Regulatory and growth metrics for fintech companies',
        driver_count: 6, formula_count: 15, benchmark_count: 12, workflow_count: 5,
        status: 'archived', scope: 'global', category: 'Finance', updated_at: '2023-12-01T09:00:00Z', version: '0.5.0',
      },
    };
    const pack = allPacks[packId];
    if (!pack) {
      return HttpResponse.json({ error: 'Pack not found' }, { status: 404 });
    }
    return HttpResponse.json(pack);
  }),

  http.post(`${API_BASE}${L3_PREFIX}/packs/:packId/apply`, async ({ params, request }) => {
    await delay(300);
    const packId = params.packId as string;
    const body = (await request.json()) as { entity_id?: string };

    // Simulate error for specific test case
    if (packId === 'error-pack') {
      return HttpResponse.json(
        { error: 'Failed to apply pack: Entity not found' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      success: true,
      pack_id: packId,
      entity_id: body?.entity_id || 'default-entity',
      applied_at: new Date().toISOString(),
      applied_drivers: 3,
      applied_formulas: 5,
    });
  }),
];

// ===== Health Monitor Mocks (L4) =====

export const healthMocks = [
  // System health endpoint
  http.get(`${API_BASE}${L4_PREFIX}/health`, async () => {
    await delay(100);
    return HttpResponse.json({
      overall_status: 'healthy',
      services: [
        { name: 'l1-ingestion', status: 'healthy', response_time_ms: 45, last_check: new Date().toISOString() },
        { name: 'l2-extraction', status: 'healthy', response_time_ms: 120, last_check: new Date().toISOString() },
        { name: 'l3-knowledge', status: 'healthy', response_time_ms: 80, last_check: new Date().toISOString() },
        { name: 'l4-agents', status: 'healthy', response_time_ms: 60, last_check: new Date().toISOString() },
        { name: 'l5-ground-truth', status: 'healthy', response_time_ms: 55, last_check: new Date().toISOString() },
      ],
      summary: { healthy: 5, degraded: 0, unhealthy: 0, unknown: 0 },
      timestamp: new Date().toISOString(),
    });
  }),

  // Health alerts endpoint
  http.get(`${API_BASE}${L4_PREFIX}/health/alerts`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'alert-1',
        severity: 'info',
        service: 'l1-ingestion',
        message: 'All systems operational',
        timestamp: new Date().toISOString(),
        acknowledged: false,
      },
    ]);
  }),
];

// ===== Tenant Settings Mocks (L4) =====

export const tenantSettingsMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/tenant/settings`, async () => {
    await delay(100);
    return HttpResponse.json({
      tenant_id: 'test-tenant-123',
      name: 'Test Tenant',
      slug: 'test-tenant',
      tier: 'advanced',
      features: {
        advanced_mode: true,
        beta_features: false,
      },
      limits: {
        max_workflows: 100,
        max_entities: 10000,
      },
    });
  }),
];

// ===== User Management Mocks (L4) =====

export const userMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/users`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const role = url.searchParams.get('role');

    let users = [
      {
        id: 'user-1',
        email: 'admin@example.com',
        name: 'Admin User',
        role: 'admin',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        last_login: '2024-01-15T10:00:00Z',
      },
      {
        id: 'user-2',
        email: 'user@example.com',
        name: 'Standard User',
        role: 'standard',
        status: 'active',
        created_at: '2024-01-05T00:00:00Z',
        last_login: '2024-01-14T09:00:00Z',
      },
    ];

    if (role) {
      users = users.filter(u => u.role === role);
    }

    return HttpResponse.json(users);
  }),

  http.get(`${API_BASE}${L4_PREFIX}/users/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      email: 'user@example.com',
      name: 'Test User',
      role: 'standard',
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
      last_login: '2024-01-15T10:00:00Z',
    });
  }),

  // API Keys management
  http.get(`${API_BASE}${L4_PREFIX}/api-keys`, async () => {
    await delay(100);
    return HttpResponse.json([
      {
        id: 'key-1',
        name: 'Production API Key',
        key_prefix: 'pk_live_',
        permissions: ['read', 'write'],
        created_at: '2024-01-01T00:00:00Z',
        last_used: '2024-01-15T10:00:00Z',
        expires_at: null,
      },
      {
        id: 'key-2',
        name: 'Read-only Key',
        key_prefix: 'pk_test_',
        permissions: ['read'],
        created_at: '2024-01-05T00:00:00Z',
        last_used: '2024-01-14T09:00:00Z',
        expires_at: '2024-12-31T00:00:00Z',
      },
    ]);
  }),

  http.post(`${API_BASE}${L4_PREFIX}/api-keys`, async ({ request }) => {
    await delay(150);
    const body = (await request.json()) as { name?: string; permissions?: string[] };
    return HttpResponse.json({
      id: `key-${Date.now()}`,
      name: body?.name || 'New API Key',
      key: `pk_live_${Math.random().toString(36).substring(2, 15)}`,
      permissions: body?.permissions || ['read'],
      created_at: new Date().toISOString(),
      last_used: null,
      expires_at: null,
    }, { status: 201 });
  }),

  http.delete(`${API_BASE}${L4_PREFIX}/api-keys/:id`, async ({ params }) => {
    await delay(100);
    return HttpResponse.json({
      id: params.id,
      deleted: true,
      deleted_at: new Date().toISOString(),
    });
  }),
];

// ===== Error Simulation Mocks =====

export const errorMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/error/500`, () => {
    return HttpResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/error/404`, () => {
    return HttpResponse.json({ error: 'Not Found' }, { status: 404 });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/error/timeout`, async () => {
    await delay(30000); // Will trigger timeout
    return HttpResponse.json({ error: 'Timeout' });
  }),
];

// ===== L6 Benchmark Dataset Mocks =====
export const l6BenchmarkMocks = [
  http.get(`${API_BASE}${L6_PREFIX}/datasets`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');
    const status = url.searchParams.get('status');
    const confidence = url.searchParams.get('confidence');

    let benchmarks = [
      {
        id: 'bench-1',
        benchmark_id: 'bench-1',
        name: 'Industry Average ROI',
        industry: industry || 'Software',
        vertical: 'SaaS',
        value_range: '2.5x - 4.0x',
        confidence: 'High',
        source: 'Industry Research',
        year: 2024,
        status: 'active',
        tags: ['roi', 'saas'],
        usage_count: 15,
      },
      {
        id: 'bench-2',
        benchmark_id: 'bench-2',
        name: 'Implementation Timeline',
        industry: industry || 'Software',
        vertical: 'Enterprise',
        value_range: '3-6 months',
        confidence: 'Medium',
        source: 'Survey Data',
        year: 2024,
        status: 'active',
        tags: ['timeline'],
        usage_count: 8,
      },
    ];

    if (status) benchmarks = benchmarks.filter((b: any) => b.status === status);
    if (confidence) benchmarks = benchmarks.filter((b: any) => b.confidence === confidence);

    return HttpResponse.json(benchmarks);
  }),

  http.get(`${API_BASE}${L6_PREFIX}/datasets/:id`, async ({ params }) => {
    await delay(100);
    const id = params.id as string;
    return HttpResponse.json({
      id,
      benchmark_id: id,
      name: 'Detailed Benchmark',
      industry: 'Software',
      value_range: '2.5x - 4.0x',
      confidence: 'High',
      source: 'Industry Research',
      year: 2024,
      status: 'active',
      tags: ['detailed'],
      usage_count: 10,
    });
  }),
];

// ===== L5 Governance Mocks =====
export const governanceMocks = [
  http.get(`${API_BASE}${L5_PREFIX}/truths`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const limit = url.searchParams.get('limit');

    let items = [
      { id: 'truth-1', claim: 'Revenue increase', claim_type: 'financial', status: 'validated', maturity_level: 3, confidence: 0.85, is_stale: false, updated_at: '2024-01-15T10:00:00Z' },
      { id: 'truth-2', claim: 'Cost reduction', claim_type: 'operational', status: 'pending', maturity_level: 2, confidence: 0.65, is_stale: false, updated_at: '2024-01-14T09:00:00Z' },
    ];

    if (status) items = items.filter((t: any) => t.status === status);

    return HttpResponse.json({
      items: limit ? items.slice(0, parseInt(limit, 10)) : items,
      total: items.length,
      limit: limit ? parseInt(limit, 10) : 25,
      offset: 0,
      has_more: false,
    });
  }),

  http.get(`${API_BASE}${L5_PREFIX}/maturity-ladder`, async () => {
    await delay(100);
    return HttpResponse.json({
      levels: [
        { level: 1, name: 'Initial', description: 'Basic validation', required_status: 'extracted', advancement_trigger: 'Manual review' },
        { level: 2, name: 'Developing', description: 'Partial evidence', required_status: 'supported', advancement_trigger: 'Evidence attached' },
        { level: 3, name: 'Mature', description: 'Strong evidence', required_status: 'corroborated', advancement_trigger: 'Multi-source verified' },
        { level: 4, name: 'Optimized', description: 'Continuous validation', required_status: 'approved', advancement_trigger: 'Auto-validation passed' },
      ],
    });
  }),

  http.get(`${API_BASE}${L5_PREFIX}/truths/freshness-summary`, async () => {
    await delay(100);
    return HttpResponse.json({
      stale_count: 0,
      fresh_count: 2,
      expiring_soon_count: 0,
      total_count: 2,
    });
  }),

  http.get(`${API_BASE}${L5_PREFIX}/truths/stale`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const limit = url.searchParams.get('limit');
    const items: any[] = [];
    return HttpResponse.json({
      items: limit ? items.slice(0, parseInt(limit, 10)) : items,
      total: items.length,
      limit: limit ? parseInt(limit, 10) : 25,
      offset: 0,
      has_more: false,
    });
  }),

  http.get(`${API_BASE}${L5_PREFIX}/truths/:truthId/audit`, async ({ params }) => {
    await delay(100);
    const truthId = params.truthId as string;
    if (truthId === 'broken') {
      return new HttpResponse(JSON.stringify({ error: 'Audit service unavailable' }), { status: 500 });
    }
    return HttpResponse.json([
      { id: 'audit-1', timestamp: '2024-01-15T10:00:00Z', action: 'created', actor: 'user@example.com', notes: 'Initial creation' },
    ]);
  }),
];

// ===== Graph Query Double-Prefix Mocks (frontend calls /graph/subgraph via apiClient l3) =====
export const graphQueryFixMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/graph/subgraph`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const query = url.searchParams.get('query') || '';
    const centerEntityId = url.searchParams.get('center_entity_id');
    const depth = parseInt(url.searchParams.get('depth') || '2', 10);
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);

    const nodes = [
      { id: 'ent-1', name: query || 'Root', entity_type: 'capability', confidence_score: 0.95 },
      { id: 'ent-2', name: 'Related', entity_type: 'usecase', confidence_score: 0.88 },
    ];

    return HttpResponse.json({
      root_entity_id: centerEntityId || '',
      nodes: nodes.slice(0, limit),
      edges: [
        { source: 'ent-1', target: 'ent-2', type: 'RELATED_TO', properties: {} },
      ],
      depth,
      stats: {
        total_nodes: nodes.length,
        total_edges: 1,
        density: 0.5,
      },
    });
  }),
];

// ===== ValuePack Framework Mocks (v1.0) =====
export const valuePackFrameworkMocks = [
  http.get(`${API_BASE}${L3_PREFIX}/valuepacks`, async ({ request }) => {
    await delay(100);
    const url = new URL(request.url);
    const tier = url.searchParams.get('tier');
    const search = url.searchParams.get('search');

    let items = [
      {
        id: 'vpf-1',
        industry_id: 'software-saas',
        industry_name: 'Software / SaaS',
        tier: 1,
        description: 'SaaS value framework',
        driver_count: 5,
        formula_count: 8,
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 'vpf-2',
        industry_id: 'financial-services',
        industry_name: 'Financial Services',
        tier: 2,
        description: 'FinServ value framework',
        driver_count: 7,
        formula_count: 12,
        updated_at: '2024-01-14T09:00:00Z',
      },
    ];

    if (tier) items = items.filter((i: any) => i.tier === parseInt(tier, 10));
    if (search) items = items.filter((i: any) => i.industry_name.toLowerCase().includes(search.toLowerCase()));

    return HttpResponse.json({ items, total: items.length });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/valuepacks/ontology-map`, async () => {
    await delay(100);
    return HttpResponse.json({
      domains: ['Finance', 'IT', 'Healthcare', 'Manufacturing'],
      entity_types: ['Capability', 'Outcome', 'Persona', 'Process'],
      relationship_types: ['ENABLES', 'DEPENDS_ON', 'DRIVES', 'USES'],
    });
  }),

  http.get(`${API_BASE}${L3_PREFIX}/valuepacks/composable-templates`, async () => {
    await delay(100);
    return HttpResponse.json({
      templates: [
        { id: 'tpl-1', name: 'ROI Calculator', category: 'financial', composable: true },
        { id: 'tpl-2', name: 'TVM Analysis', category: 'financial', composable: true },
      ],
    });
  }),
];

// ===== Opportunities Mocks =====
export const opportunityMocks = [
  http.get(`${API_BASE}${L4_PREFIX}/discover/opportunities`, async () => {
    await delay(100);
    return HttpResponse.json({
      opportunities: [
        { id: 'opp-1', title: 'Cost Optimization', potential_value: 1200000, confidence: 0.85, status: 'open' },
        { id: 'opp-2', title: 'Revenue Growth', potential_value: 2500000, confidence: 0.72, status: 'open' },
      ],
      total: 2,
    });
  }),
];

// ===== Combine all handlers =====

export const handlers = [
  ...authMocks,
  ...workflowMocks,
  ...jobStreamMocks,
  ...graphMocks,
  ...graphQueryFixMocks,
  ...benchmarkMocks,
  ...l6BenchmarkMocks,
  ...formulaMocks,
  ...variableMocks,
  ...provenanceMocks,
  ...businessCaseMocks,
  ...valuePackMocks,
  ...valuePackFrameworkMocks,
  ...valueTreeMocks,
  ...healthMocks,
  ...tenantSettingsMocks,
  ...userMocks,
  ...governanceMocks,
  ...opportunityMocks,
  ...errorMocks,
];
