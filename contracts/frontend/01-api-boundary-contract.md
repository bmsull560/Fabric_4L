# Contract A: API Boundary Contract

**Status:** Ratified  
**Version:** 1.0.0  
**Date:** 2026-04-26  
**Scope:** All frontend-to-backend HTTP communication in Fabric 4L  
**Enforcement:** CI gate `api_boundary_check` (see Section 7)

---

## 1. Purpose

This contract defines the standardized rules governing how every frontend hook communicates with every backend endpoint. It eliminates the 15+ competing error handling patterns, the absence of pagination standards, and the inconsistent retry policies identified in the frontend audit.

All frontend code that makes HTTP requests MUST conform to this contract. Non-conforming code is a build failure.

---

## 2. Single HTTP Gateway

All HTTP traffic from the frontend to any backend layer MUST pass through `apiClient.ts`. No component, hook, or utility may import `axios`, `fetch`, or any other HTTP primitive directly.

| Rule | Requirement |
|------|-------------|
| Import restriction | Only `apiClient.ts` may import `axios` |
| Layer routing | All requests specify a `LayerKey` (`l1`–`l6`) |
| Tenant injection | `X-Tenant-ID` header is injected by `apiClient` interceptor |
| Auth injection | Bearer token is injected by `apiClient` interceptor |
| Request ID | `X-Request-ID` UUID is stamped on every outgoing request |

---

## 3. Error Shape Contract

Every backend error response MUST be normalized into a `FabricApiError` before crossing the hook boundary. Domain-specific error classes extend `BaseApiError`.

### 3.1 Canonical Error Shape

```typescript
interface FabricApiError {
  statusCode: number;       // HTTP status code
  code: string;             // Machine-readable error code (e.g., "TENANT_MISMATCH")
  message: string;          // Human-readable message
  requestId: string;        // Correlation ID from X-Request-ID
  timestamp: string;        // ISO 8601 timestamp
  retryable: boolean;       // Whether the client should retry
  details?: unknown;        // Optional structured error details
}
```

### 3.2 Error Classification

| HTTP Status | Classification | UI Treatment | Retryable |
|-------------|---------------|--------------|-----------|
| 400 | Validation Error | Field-level error display | No |
| 401 | Authentication Error | Redirect to login | No |
| 403 | Permission Error | "Insufficient permissions" banner | No |
| 404 | Not Found | "Resource not found" with navigation | No |
| 409 | Conflict | "Resource was modified" with refresh | Yes |
| 422 | Unprocessable Entity | Form-level error display | No |
| 429 | Rate Limited | Auto-retry with backoff | Yes |
| 500 | Server Error | "Something went wrong" with retry button | Yes |
| 502/503/504 | Gateway Error | "Service temporarily unavailable" | Yes |

### 3.3 Retry Policy

All retryable errors use exponential backoff with jitter:

```typescript
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: (attempt: number) => Math.min(1000 * 2 ** attempt + Math.random() * 500, 30000),
  retryCondition: (error: FabricApiError) => error.retryable,
};
```

---

## 4. Pagination Contract

All list endpoints MUST use cursor-based or offset-based pagination with a standardized request/response shape.

### 4.1 Request Parameters

```typescript
interface PaginationParams {
  page?: number;           // 1-indexed page number (offset-based)
  page_size?: number;      // Items per page (default: 25, max: 100)
  cursor?: string;         // Opaque cursor (cursor-based)
  sort_by?: string;        // Field name to sort by
  sort_order?: 'asc' | 'desc';  // Sort direction
}
```

### 4.2 Response Shape

```typescript
interface PaginatedResponse<T> {
  items: T[];              // The page of results
  total: number;           // Total count across all pages
  page: number;            // Current page number
  page_size: number;       // Items per page
  has_next: boolean;       // Whether more pages exist
  next_cursor?: string;    // Cursor for next page (cursor-based)
}
```

---

## 5. Request Validation

All mutation requests (POST, PUT, PATCH, DELETE) MUST validate the request payload against a Zod schema before dispatching. GET requests validate query parameters.

```typescript
// Every protocol hook validates before sending
const validatedPayload = requestSchema.parse(payload);
const response = await apiClient.post(layer, path, validatedPayload);
const validatedResponse = responseSchema.parse(response.data);
```

---

## 6. Cache Policy Standards

| Data Category | Stale Time | Refetch On Window Focus | Example |
|--------------|------------|------------------------|---------|
| List data | 30 seconds | Yes | Account list, product list |
| Detail data | 60 seconds | Yes | Account detail, hypothesis detail |
| Activity/stream data | 10 seconds | Yes | Enrichment status, signals |
| Reference data | 5 minutes | No | Templates, benchmarks, industries |
| Configuration | 10 minutes | No | Platform settings |

---

## 7. CI Enforcement

The `api_boundary_check` CI gate scans all files in `src/` for:

1. Direct `axios` or `fetch` imports outside `apiClient.ts` — **build failure**
2. Missing Zod schema on mutation hooks — **build warning** (failure after Sprint 4)
3. Inline retry configuration instead of `RETRY_CONFIG` — **build warning**
4. Error handling that does not extend `BaseApiError` — **build warning**

---

## 8. Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-04-26 | Initial ratification |
