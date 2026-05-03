# User Workflow API Contracts

This document summarizes the key API contracts used in the core user workflow from prospect input through intelligence generation, hypothesis development, and value model building.

## Overview

The core user workflow interacts with several backend services across the Value Fabric platform:

- **Account Management API** (Layer 1/2)
- **Value Hypothesis API** (Layer 4)
- **Workspace Intelligence API** (Layer 4)
- **ROI Calculator API** (Layer 3 DIL)
- **Industry Benchmarks API** (Layer 6 DIL)

## Account Management API

### Create Account

Creates a new account in the system from prospect input.

**Endpoint**: `POST /api/v1/accounts`

**Request**:

```typescript
{
  name: string;              // Company name (required)
  domain?: string;           // Company website domain
  industry?: string;         // Industry classification
  stage?: string;            // Account stage (e.g., "prospect")
  enrichment_input?: string;  // Structured prompt text
}
```

**Response**:

```typescript
{
  account: {
    id: string;              // Account UUID
    name: string;
    domain?: string;
    industry?: string;
    stage: string;
    annual_revenue?: number;
    created_at: string;      // ISO 8601 timestamp
    updated_at: string;      // ISO 8601 timestamp
  }
}
```

**Example**:

```bash
curl -X POST https://api.valuefabric.com/api/v1/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "name": "Medtronic",
    "domain": "medtronic.com",
    "industry": "Medical Devices",
    "stage": "prospect",
    "enrichment_input": "Buying context: New product launch readiness..."
  }'
```

**Error Responses**:

- `400 Bad Request`: Invalid input data
- `409 Conflict`: Account already exists
- `422 Unprocessable Entity`: Validation error

---

### Get Account

Retrieves account details by ID.

**Endpoint**: `GET /api/v1/accounts/:id`

**Response**:

```typescript
{
  account: {
    id: string;
    name: string;
    domain?: string;
    industry?: string;
    stage: string;
    annual_revenue?: number;
    enrichment_input?: string;
    created_at: string;
    updated_at: string;
  }
}
```

---

## Value Hypothesis API

### Generate Hypotheses

Generates AI-backed value hypotheses for an account based on intelligence data.

**Endpoint**: `POST /api/v1/value-hypotheses/generate`

**Request**:

```typescript
{
  account_id: string;        // Account UUID (required)
  max_hypotheses?: number;   // Maximum number of hypotheses (default: 20)
  options?: {
    include_strategic?: boolean;
    min_confidence?: number;  // Minimum confidence threshold (0-1)
  }
}
```

**Response**:

```typescript
{
  hypotheses: {
    id: string;
    account_id: string;
    value_driver: string;     // Name of the value driver
    hypothesis_text: string; // Hypothesis description
    confidence: number;      // Confidence score (0-1)
    product_id: string;      // Mapped product ID
    status: "draft" | "validated" | "rejected" | "converted";
    signal_ids: string[];    // Supporting signal IDs
    evidence_ids: string[];  // Supporting evidence IDs
    created_at: string;
    updated_at: string;
  }[];
  metadata: {
    total_generated: number;
    avg_confidence: number;
    generation_time_ms: number;
  }
}
```

**Example**:

```bash
curl -X POST https://api.valuefabric.com/api/v1/value-hypotheses/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "account_id": "acct-123e4567-e89b-12d3-a456-426614174000",
    "max_hypotheses": 20,
    "options": {
      "min_confidence": 0.5
    }
  }'
```

**Error Responses**:

- `400 Bad Request`: Invalid account_id or options
- `404 Not Found`: Account not found
- `422 Unprocessable Entity`: Insufficient enrichment data
- `503 Service Unavailable`: LLM service unavailable

---

### Get Account Hypotheses

Retrieves all hypotheses for a specific account.

**Endpoint**: `GET /api/v1/value-hypotheses/account/:account_id`

**Query Parameters**:

- `status` (optional): Filter by status (`draft`, `validated`, `rejected`, `converted`)
- `min_confidence` (optional): Filter by minimum confidence (0-1)
- `limit` (optional): Maximum number of results (default: 100)

**Response**:

```typescript
{
  hypotheses: {
    id: string;
    account_id: string;
    value_driver: string;
    hypothesis_text: string;
    confidence: number;
    product_id: string;
    status: string;
    signal_ids: string[];
    evidence_ids: string[];
    validation_notes?: string;
    created_at: string;
    updated_at: string;
  }[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  }
}
```

**Example**:

```bash
curl -X GET "https://api.valuefabric.com/api/v1/value-hypotheses/account/acct-123?status=validated&min_confidence=0.7" \
  -H "Authorization: Bearer {token}"
```

---

### Validate Hypothesis

Updates the validation status of a hypothesis.

**Endpoint**: `POST /api/v1/value-hypotheses/:id/validate`

**Request**:

```typescript
{
  status: "validated" | "rejected" | "converted";
  validation_notes?: string;  // Optional notes explaining the decision
}
```

**Response**:

```typescript
{
  hypothesis: {
    id: string;
    status: string;
    validation_notes?: string;
    updated_at: string;
  }
}
```

**Example**:

```bash
curl -X POST https://api.valuefabric.com/api/v1/value-hypotheses/hyp-456/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "status": "validated",
    "validation_notes": "Strong evidence from recent press release"
  }'
```

**Error Responses**:

- `400 Bad Request`: Invalid status value
- `404 Not Found`: Hypothesis not found
- `409 Conflict`: Hypothesis already converted

---

## Workspace Intelligence API

### Generate Workspace Intelligence

Triggers intelligence generation for a specific workspace tab.

**Endpoint**: `POST /api/v1/workspace/cases/:caseId/intelligence`

**Request**:

```typescript
{
  tab_id: string;            // Tab to generate intelligence for
  options?: {
    depth?: "light" | "standard" | "deep";
    use_web_enrichment?: boolean;
    use_prior_context?: boolean;
    compliance_sensitive?: boolean;
  }
}
```

**Response**:

```typescript
{
  case_id: string;
  tab_id: string;
  status: "generating" | "complete" | "failed";
  started_at: string;
  estimated_completion_at?: string;
  error?: string;
}
```

**Example**:

```bash
curl -X POST https://api.valuefabric.com/api/v1/workspace/cases/case-789/intelligence \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "tab_id": "hypotheses",
    "options": {
      "depth": "deep",
      "use_web_enrichment": true
    }
  }'
```

---

### Get Workspace Tab Data

Retrieves data for a specific workspace tab.

**Endpoint**: `GET /api/v1/workspace/cases/:caseId/tabs/:tabId`

**Response**:

```typescript
{
  case_id: string;
  tab_id: string;
  data: {
    // Tab-specific data structure
    // Example for value-model tab:
    valueLines?: {
      id: string;
      driver: string;
      category: "hard" | "strategic";
      conservative: number;
      expected: number;
      optimistic: number;
      source: string;
    }[];
    // Example for hypotheses tab:
    hypotheses?: {
      id: string;
      value_driver: string;
      hypothesis_text: string;
      confidence: number;
      status: string;
    }[];
  };
  updated_at: string;
}
```

**Example**:

```bash
curl -X GET https://api.valuefabric.com/api/v1/workspace/cases/case-789/tabs/value-model \
  -H "Authorization: Bearer {token}"
```

---

### Persist Workspace Tab Data

Saves data for a specific workspace tab.

**Endpoint**: `PUT /api/v1/workspace/cases/:caseId/tabs/:tabId`

**Request**:

```typescript
{
  data: {
    // Tab-specific data structure (same as GET response)
  }
}
```

**Response**:

```typescript
{
  case_id: string;
  tab_id: string;
  updated_at: string;
}
```

---

## ROI Calculator API (DIL)

### Calculate ROI

Calculates ROI metrics based on value model inputs.

**Endpoint**: `POST /api/v1/roi/calculate`

**Request**:

```typescript
{
  deal_size: number;          // Total deal size (annual benefit)
  annual_benefit: number;      // Annual benefit amount
  implementation_cost: number; // Implementation cost (often % of deal_size)
  discount_rate: number;       // Discount rate for NPV (e.g., 0.1 for 10%)
  time_horizon_years: number;  // Time horizon for ROI (e.g., 3)
  account_id?: string;         // Optional account ID for benchmarking
  scenario?: string;          // Scenario label (e.g., "expected")
}
```

**Response**:

```typescript
{
  calculation_id: string;
  npv: number;                // Net Present Value
  irr: number;                // Internal Rate of Return (decimal, e.g., 0.15 for 15%)
  payback_months: number;     // Payback period in months
  total_roi_pct: number;      // Total ROI percentage (e.g., 350 for 350%)
  scenario_results: {
    scenario: string;
    npv: number;
    irr: number;
    payback_months: number;
    roi_pct: number;
  }[];
  assumptions: {
    discount_rate: number;
    time_horizon_years: number;
    implementation_cost_pct: number;
  }
  calculated_at: string;
}
```

**Example**:

```bash
curl -X POST https://api.valuefabric.com/api/v1/roi/calculate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "deal_size": 2500000,
    "annual_benefit": 2500000,
    "implementation_cost": 750000,
    "discount_rate": 0.1,
    "time_horizon_years": 3,
    "account_id": "acct-123",
    "scenario": "expected"
  }'
```

**Error Responses**:

- `400 Bad Request`: Invalid input values
- `422 Unprocessable Entity`: Calculation failed (e.g., division by zero)
- `503 Service Unavailable**: ROI calculator service down

---

### Get ROI Templates

Retrieves available ROI calculation templates.

**Endpoint**: `GET /api/v1/roi/templates`

**Response**:

```typescript
{
  templates: {
    id: string;
    name: string;
    description: string;
    default_discount_rate: number;
    default_time_horizon_years: number;
    default_implementation_cost_pct: number;
    industry?: string;
  }[];
}
```

**Example**:

```bash
curl -X GET https://api.valuefabric.com/api/v1/roi/templates \
  -H "Authorization: Bearer {token}"
```

---

## Industry Benchmarks API (DIL)

### Get Industry Benchmarks

Retrieves industry benchmark data for ROI comparisons.

**Endpoint**: `GET /api/v1/roi/benchmarks/:industry`

**Path Parameters**:

- `industry`: Industry name (e.g., "Medical Devices", "Financial Services")

**Query Parameters**:

- `year` (optional): Benchmark year (default: current year)
- `region` (optional): Geographic region (default: global)

**Response**:

```typescript
{
  industry: string;
  year: number;
  region: string;
  sample_size: number;         // Number of companies in benchmark
  avg_roi_pct: number;         // Average ROI percentage
  avg_payback_months: number;  // Average payback period in months
  avg_npv: number;             // Average NPV
  percentiles: {
    p25: {
      roi_pct: number;
      payback_months: number;
      npv: number;
    };
    p50: {
      roi_pct: number;
      payback_months: number;
      npv: number;
    };
    p75: {
      roi_pct: number;
      payback_months: number;
      npv: number;
    };
    p90: {
      roi_pct: number;
      payback_months: number;
      npv: number;
    };
  };
  updated_at: string;
}
```

**Example**:

```bash
curl -X GET "https://api.valuefabric.com/api/v1/roi/benchmarks/Medical%20Devices?year=2024&region=US" \
  -H "Authorization: Bearer {token}"
```

**Error Responses**:

- `404 Not Found`: Industry benchmarks not available
- `400 Bad Request`: Invalid industry name

---

### List Available Industries

Lists all industries with available benchmark data.

**Endpoint**: `GET /api/v1/roi/benchmarks`

**Response**:

```typescript
{
  industries: {
    name: string;
    sector: string;
    sample_size: number;
    last_updated: string;
  }[];
}
```

**Example**:

```bash
curl -X GET https://api.valuefabric.com/api/v1/roi/benchmarks \
  -H "Authorization: Bearer {token}"
```

---

## Error Handling

### Standard Error Response Format

All API endpoints return errors in the following format:

```typescript
{
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable error message
    details?: any;          // Additional error details
    request_id: string;     // Request ID for tracing
    timestamp: string;       // ISO 8601 timestamp
  }
}
```

### Common Error Codes

- `INVALID_REQUEST`: Malformed request or invalid parameters
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., duplicate)
- `RATE_LIMITED`: Rate limit exceeded
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable
- `INTERNAL_ERROR`: Unexpected server error

### Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Standard limit**: 100 requests per minute per user
- **Burst limit**: 200 requests per minute per user
- **Headers**:
  - `X-RateLimit-Limit`: Request limit per minute
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

### Retry Strategy

For transient errors (rate limits, service unavailable), use exponential backoff:

```typescript
async function fetchWithRetry(url: string, options: RequestInit, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;
      
      if (response.status === 429 || response.status === 503) {
        const retryAfter = response.headers.get('Retry-After');
        const delay = retryAfter 
          ? parseInt(retryAfter) * 1000 
          : Math.pow(2, i) * 1000; // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      throw new Error(`Request failed: ${response.status}`);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
}
```

---

## Authentication

All API endpoints require authentication via Bearer token:

```bash
curl -X GET https://api.valuefabric.com/api/v1/accounts \
  -H "Authorization: Bearer {your_jwt_token}"
```

**Token Format**: JWT (JSON Web Token)  
**Token Source**: Obtained from `/auth/login` or `/auth/refresh`  
**Token Expiration**: Typically 1 hour (refresh via `/auth/refresh`)

---

## Pagination

List endpoints support pagination via query parameters:

- `limit`: Maximum number of items per page (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

**Response Format**:

```typescript
{
  data: any[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }
}
```

---

## Related Documentation

- [Core User Workflow](../workflows/core-user-workflow.md)
- [Component Interaction Map](../architecture/component-interaction-map.md)
- [Data Intelligence Layer Architecture](../../value-fabric/docs/data-intelligence-layer.md)
- [API Reference](../API_REFERENCE.md)
