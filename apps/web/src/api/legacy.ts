/**
 * @fileoverview Legacy API Types and Schemas
 *
 * DEPRECATED exports that have been superseded by OpenAPI-aligned types.
 * These remain available for backward compatibility only.
 * New code MUST NOT import from this module.
 *
 * @deprecated All exports in this file are deprecated. Use canonical types
 * from `@/api/workflows`, `@/hooks/useWorkflows`, or generated API clients.
 */

import { z } from "zod";

// ============================================================================
// Deprecated Workflow Schemas (superseded by @/api/workflows)
// ============================================================================

/**
 * @deprecated Use `WorkflowStatusEnum` from contract helpers or types
 * from `@/api/workflows` instead. This schema uses `active` status which
 * does not exist in the backend API.
 */
export const WorkflowSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  status: z.enum(["active", "paused", "completed", "failed"]),
  last_run: z.string().datetime({ message: "Invalid datetime" }).optional(),
  configuration: z.record(z.string(), z.unknown()).optional(),
});

/**
 * @deprecated Use types from `@/api/workflows` instead.
 */
export const WorkflowExecutionSchema = z.object({
  id: z.string().uuid(),
  workflow_id: z.string().uuid(),
  status: z.enum(["pending", "running", "completed", "failed"]),
  started_at: z.string().datetime({ message: "Invalid datetime" }),
  completed_at: z.string().datetime({ message: "Invalid datetime" }).optional(),
  results: z.record(z.string(), z.unknown()).optional(),
  logs: z.array(
    z.object({
      timestamp: z.string().datetime({ message: "Invalid datetime" }),
      level: z.enum(["info", "warning", "error"]),
      message: z.string(),
    }),
  ),
});

// ============================================================================
// Deprecated Workflow Interfaces (superseded by @/hooks/useWorkflows)
// ============================================================================

/**
 * @deprecated Use `Workflow` from `@/hooks/useWorkflows` instead.
 * This legacy type does not align with the L4 API. Status values
 * (`active`) and fields (`last_run`, `configuration`) do not exist
 * in the backend schema.
 */
export interface Workflow {
  id: string;
  name: string;
  status: "active" | "paused" | "completed" | "failed";
  last_run?: string;
  configuration?: Record<string, unknown>;
}

/**
 * @deprecated Use types from `@/api/workflows` instead.
 * This legacy type predates the OpenAPI-aligned workflow API.
 */
export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
  results?: Record<string, unknown>;
  logs: Array<{
    timestamp: string;
    level: "info" | "warning" | "error";
    message: string;
  }>;
}
