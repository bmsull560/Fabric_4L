/**
 * Middleware Pipeline - Canonical Implementation
 *
 * CONTRACT.md §2.3 - Middleware and Auth Flow
 *
 * Eight-phase middleware stack with declarable, composable phases.
 * Each phase is a pure function that takes a context object and returns
 * a modified context or throws an error.
 *
 * Copy this file as the starting point for the middleware pipeline in new services.
 */

import type { TenantContext } from "../context/tenant-context";
import type { CanonicalError } from "../errors/error-shape";

// ============================================================================
// Types
// ============================================================================

/** HTTP methods supported by the pipeline */
export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS" | "HEAD";

/** Request context passed through all phases */
export interface RequestContext {
  /** Unique request identifier */
  requestId: string;

  /** Correlation ID for distributed tracing */
  traceId: string;

  /** OpenTelemetry span context */
  span?: unknown;

  /** Authenticated identity (set by auth phase) */
  identity?: {
    subjectId: string;
    authMethod: "jwt" | "api_key" | "certificate";
  };

  /** Tenant context (set by auth phase) */
  tenantContext?: TenantContext;

  /** Validated request body (set by validation phase) */
  validatedBody?: unknown;

  /** Validated query/path params (set by validation phase) */
  validatedParams?: Record<string, unknown>;

  /** Handler result (set by handler phase) */
  result?: unknown;

  /** Raw HTTP request (minimal abstraction) */
  raw: {
    method: HttpMethod;
    path: string;
    headers: Record<string, string | string[] | undefined>;
    body: unknown;
  };
}

/** Response context for serialization */
export interface ResponseContext {
  statusCode: number;
  headers: Record<string, string>;
  body: unknown;
}

/** Phase handler function type */
export type PhaseHandler = (ctx: RequestContext) => RequestContext | Promise<RequestContext>;

/** Phase that can terminate the pipeline */
export type TerminatingPhase = (
  ctx: RequestContext
) => Promise<{ terminated: true; response: ResponseContext } | { terminated: false; context: RequestContext }>;

/** Phase definition */
export interface Phase {
  name: PhaseName;
  order: number;
  handler: PhaseHandler | TerminatingPhase;
  canTerminate: boolean;
}

/** The eight canonical phase names */
export type PhaseName =
  | "request_id"
  | "correlation"
  | "auth"
  | "tenant_scope"
  | "rate_limit"
  | "validation"
  | "handler"
  | "response";

/** Route manifest entry */
export interface RouteDefinition {
  /** URL pattern (e.g., "/users/:id") */
  path: string;

  /** HTTP method */
  method: HttpMethod;

  /** Required phase names for this route */
  phases: PhaseName[];

  /** Business logic handler (phase 7) */
  handler: (ctx: RequestContext) => Promise<unknown>;

  /** OpenAPI operation ID */
  operationId: string;
}

// ============================================================================
// Pipeline Implementation
// ============================================================================

/**
 * Canonical middleware pipeline implementing the eight-phase stack.
 *
 * CONTRACT.md §2.3:
 * - Phases are pure functions (no side effects except auth/validation)
 * - Each phase can modify context or terminate
 * - Error boundary catches all errors and normalizes shape
 */
export class MiddlewarePipeline {
  private phases = new Map<PhaseName, Phase>();
  private routes: RouteDefinition[] = [];

  constructor() {
    this.registerDefaultPhases();
  }

  /**
   * Register a custom phase.
   *
   * CONTRACT.md §2.3:
   * - Phases must be pure functions
   * - Only auth and error_boundary can terminate
   */
  registerPhase(phase: Phase): void {
    if (this.phases.has(phase.name)) {
      throw new Error(`Phase "${phase.name}" is already registered`);
    }
    this.phases.set(phase.name, phase);
  }

  /**
   * Register a route with its phase requirements.
   *
   * CONTRACT.md §2.3:
   * - Every route must declare required phases
   * - Route manifest is validated at startup
   */
  registerRoute(route: RouteDefinition): void {
    this.validateRoutePhases(route);
    this.routes.push(route);
  }

  /**
   * Execute the pipeline for a request.
   *
   * CONTRACT.md §2.3:
   * - Phases execute in strict order
   * - Any phase can throw to trigger error_boundary
   * - Error boundary normalizes all errors to canonical shape
   */
  async execute(
    rawRequest: RequestContext["raw"],
    routePath: string
  ): Promise<ResponseContext> {
    const route = this.findRoute(routePath, rawRequest.method);
    if (!route) {
      return this.createErrorResponse(
        {
          code: "NOT_FOUND",
          message: `No route found for ${rawRequest.method} ${routePath}`,
          recoverable: false,
        },
        rawRequest
      );
    }

    // Initialize context
    let ctx: RequestContext = {
      requestId: "",
      traceId: "",
      raw: rawRequest,
    };

    try {
      // Execute phases in order
      for (const phaseName of route.phases) {
        const phase = this.phases.get(phaseName);
        if (!phase) {
          throw new Error(`Unknown phase: ${phaseName}`);
        }

        // Check if phase can terminate
        if (phase.canTerminate) {
          const result = await (phase.handler as TerminatingPhase)(ctx);
          if (result.terminated) {
            return result.response;
          }
          ctx = result.context;
        } else {
          ctx = await (phase.handler as PhaseHandler)(ctx);
        }
      }

      // Execute handler phase (phase 7)
      ctx.result = await route.handler(ctx);

      // Execute response phase (phase 8)
      const responsePhase = this.phases.get("response")!;
      const responseResult = await (responsePhase.handler as TerminatingPhase)(ctx);

      if (responseResult.terminated) {
        return responseResult.response;
      }

      // Should not reach here - response phase always terminates
      throw new Error("Response phase did not terminate pipeline");
    } catch (error) {
      // Error boundary catches all errors
      return this.errorBoundary(error, ctx);
    }
  }

  /**
   * Validate all registered routes at startup.
   *
   * CONTRACT.md §2.3:
   * - Route manifests validated at application startup
   * - Invalid configuration fails startup (cannot deploy)
   */
  validateAllRoutes(): string[] {
    const errors: string[] = [];

    for (const route of this.routes) {
      const routeErrors = this.validateRoutePhases(route);
      errors.push(...routeErrors);
    }

    return errors;
  }

  // ==========================================================================
  // Default Phases (CONTRACT.md §2.3 Table)
  // ==========================================================================

  private registerDefaultPhases(): void {
    // Phase 1: request_id - Assign x-request-id if not present
    this.registerPhase({
      name: "request_id",
      order: 1,
      canTerminate: false,
      handler: (ctx: RequestContext): RequestContext => {
        const existingId = ctx.raw.headers["x-request-id"];
        ctx.requestId = Array.isArray(existingId)
          ? existingId[0] || generateRequestId()
          : existingId || generateRequestId();
        return ctx;
      },
    });

    // Phase 2: correlation - Extract/inject correlation IDs
    this.registerPhase({
      name: "correlation",
      order: 2,
      canTerminate: false,
      handler: (ctx: RequestContext): RequestContext => {
        const traceHeader = ctx.raw.headers["x-trace-id"];
        ctx.traceId = Array.isArray(traceHeader)
          ? traceHeader[0] || ctx.requestId
          : traceHeader || ctx.requestId;
        // Initialize OpenTelemetry span
        ctx.span = { traceId: ctx.traceId, spanId: generateSpanId() };
        return ctx;
      },
    });

    // Phase 3: auth - Validate credentials, establish tenant context
    this.registerPhase({
      name: "auth",
      order: 3,
      canTerminate: true,
      handler: async (
        ctx: RequestContext
      ): Promise<
        { terminated: true; response: ResponseContext } | { terminated: false; context: RequestContext }
      > => {
        // CONTRACT.md §2.1: Auth middleware extracts tenant from JWT/headers
        const authHeader = ctx.raw.headers["authorization"];
        const tenantHeader = ctx.raw.headers["x-fabric-tenant-id"];

        if (!authHeader) {
          return {
            terminated: true,
            response: this.createErrorResponse(
              {
                code: "AUTHENTICATION_FAILED",
                message: "Authorization header required",
                recoverable: false,
              },
              ctx.raw,
              ctx.requestId,
              ctx.traceId
            ),
          };
        }

        // In production: validate JWT, extract claims, lookup tenant
        // This is simplified for the reference implementation
        ctx.identity = {
          subjectId: "user_123",
          authMethod: "jwt",
        };

        // Establish tenant context (CONTRACT.md §2.1)
        if (tenantHeader && !Array.isArray(tenantHeader)) {
          ctx.tenantContext = {
            tenant_id: tenantHeader,
            tenant_tier: "shared",
            region: "us-east-1",
            issued_at: Date.now(),
            scope: ["read", "write"],
          };
        }

        return { terminated: false, context: ctx };
      },
    });

    // Phase 4: tenant_scope - Validate tenant access
    this.registerPhase({
      name: "tenant_scope",
      order: 4,
      canTerminate: true,
      handler: async (
        ctx: RequestContext
      ): Promise<
        { terminated: true; response: ResponseContext } | { terminated: false; context: RequestContext }
      > => {
        if (!ctx.tenantContext) {
          return {
            terminated: true,
            response: this.createErrorResponse(
              {
                code: "TENANT_ACCESS_DENIED",
                message: "Tenant context required",
                recoverable: false,
              },
              ctx.raw,
              ctx.requestId,
              ctx.traceId
            ),
          };
        }

        // Validate tenant status (active, suspended, etc.)
        // In production: check if tenant is active in database

        return { terminated: false, context: ctx };
      },
    });

    // Phase 5: rate_limit - Apply rate limiting
    this.registerPhase({
      name: "rate_limit",
      order: 5,
      canTerminate: true,
      handler: async (
        ctx: RequestContext
      ): Promise<
        { terminated: true; response: ResponseContext } | { terminated: false; context: RequestContext }
      > => {
        // CONTRACT.md §2.3: Rate limit keyed by tenant_id + endpoint_pattern + identity_hash
        const key = `${ctx.tenantContext?.tenant_id || "anonymous"}:${ctx.raw.path}:${ctx.identity?.subjectId || "anon"}`;

        // In production: check rate limit against Redis/store
        const isRateLimited = false; // Placeholder

        if (isRateLimited) {
          return {
            terminated: true,
            response: this.createErrorResponse(
              {
                code: "RATE_LIMIT_EXCEEDED",
                message: "Rate limit exceeded",
                recoverable: true,
                details: { retry_after_seconds: 60 },
              },
              ctx.raw,
              ctx.requestId,
              ctx.traceId
            ),
          };
        }

        return { terminated: false, context: ctx };
      },
    });

    // Phase 6: validation - Validate request body/params against OpenAPI
    this.registerPhase({
      name: "validation",
      order: 6,
      canTerminate: true,
      handler: async (
        ctx: RequestContext
      ): Promise<
        { terminated: true; response: ResponseContext } | { terminated: false; context: RequestContext }
      > => {
        // CONTRACT.md §2.3: Validate against OpenAPI schema
        // In production: use generated validators from OpenAPI spec

        if (ctx.raw.body && typeof ctx.raw.body === "object") {
          ctx.validatedBody = ctx.raw.body;
        }

        // Parse path params
        ctx.validatedParams = extractPathParams(ctx.raw.path);

        return { terminated: false, context: ctx };
      },
    });

    // Phase 8: response - Serialize response
    this.registerPhase({
      name: "response",
      order: 8,
      canTerminate: true,
      handler: async (
        ctx: RequestContext
      ): Promise<
        { terminated: true; response: ResponseContext } | { terminated: false; context: RequestContext }
      > => {
        // CONTRACT.md §2.3: Serialize using OpenAPI response schema
        const response: ResponseContext = {
          statusCode: 200,
          headers: {
            "content-type": "application/json",
            "x-request-id": ctx.requestId,
            "x-trace-id": ctx.traceId,
          },
          body: {
            success: true,
            data: ctx.result,
            meta: {
              request_id: ctx.requestId,
              trace_id: ctx.traceId,
              timestamp: new Date().toISOString(),
            },
          },
        };

        return { terminated: true, response };
      },
    });
  }

  // ==========================================================================
  // Private Helpers
  // ==========================================================================

  private findRoute(path: string, method: HttpMethod): RouteDefinition | undefined {
    return this.routes.find((r) => r.path === path && r.method === method);
  }

  private validateRoutePhases(route: RouteDefinition): string[] {
    const errors: string[] = [];
    const requiredPhases: PhaseName[] = ["request_id", "correlation", "auth", "validation", "response"];

    for (const phase of requiredPhases) {
      if (!route.phases.includes(phase)) {
        errors.push(`Route ${route.method} ${route.path} missing required phase: ${phase}`);
      }
    }

    // Validate phase order
    let lastOrder = 0;
    for (const phaseName of route.phases) {
      const phase = this.phases.get(phaseName);
      if (phase && phase.order < lastOrder) {
        errors.push(`Route ${route.method} ${route.path} has phases out of order`);
      }
      if (phase) {
        lastOrder = phase.order;
      }
    }

    return errors;
  }

  private createErrorResponse(
    error: CanonicalError,
    rawRequest: RequestContext["raw"],
    requestId?: string,
    traceId?: string
  ): ResponseContext {
    const statusCode = mapErrorCodeToStatus(error.code);

    return {
      statusCode,
      headers: {
        "content-type": "application/json",
        "x-request-id": requestId || "unknown",
        "x-trace-id": traceId || "unknown",
      },
      body: {
        success: false,
        error,
        meta: {
          request_id: requestId || "unknown",
          trace_id: traceId || "unknown",
          timestamp: new Date().toISOString(),
        },
      },
    };
  }

  private errorBoundary(error: unknown, ctx: RequestContext): ResponseContext {
    // CONTRACT.md §2.3: Error boundary normalizes all errors to canonical shape
    const canonicalError: CanonicalError =
      error instanceof Error
        ? {
            code: "INTERNAL_ERROR",
            message: process.env.NODE_ENV === "production" ? "Internal server error" : error.message,
            recoverable: false,
          }
        : {
            code: "INTERNAL_ERROR",
            message: "An unexpected error occurred",
            recoverable: false,
          };

    console.error(`[ErrorBoundary] Request ${ctx.requestId}:`, error);

    return this.createErrorResponse(canonicalError, ctx.raw, ctx.requestId, ctx.traceId);
  }
}

// ============================================================================
// Utilities
// ============================================================================

function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateSpanId(): string {
  return `span_${Math.random().toString(36).substr(2, 16)}`;
}

function extractPathParams(path: string): Record<string, string> {
  // Simple path param extraction - production would use proper router
  const params: Record<string, string> = {};
  const segments = path.split("/");

  for (const segment of segments) {
    if (segment.starts(":")) {
      params[segment.slice(1)] = segment; // Placeholder
    }
  }

  return params;
}

function mapErrorCodeToStatus(code: string): number {
  const mapping: Record<string, number> = {
    AUTHENTICATION_FAILED: 401,
    AUTHORIZATION_DENIED: 403,
    TENANT_ACCESS_DENIED: 403,
    RATE_LIMIT_EXCEEDED: 429,
    VALIDATION_FAILED: 400,
    NOT_FOUND: 404,
    INTERNAL_ERROR: 500,
  };

  return mapping[code] || 500;
}

// ============================================================================
// Singleton Export
// ============================================================================

export const pipeline = new MiddlewarePipeline();
