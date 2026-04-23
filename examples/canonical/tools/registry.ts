/**
 * Tool Registry - Canonical Implementation
 *
 * CONTRACT.md §2.4 - Tool Invocation Boundary
 *
 * The ToolRegistry is the central catalog where all tools are declared.
 * Each tool is defined once with:
 * - Strongly-typed function with JSON Schema input contract
 * - Typed output conforming to ToolResult<T>
 * - Required permissions for authorization
 * - Framework bindings auto-generated from canonical definition
 *
 * Copy this file as the starting point for the tool system in new services.
 */

import type { ToolResult } from "../errors/error-shape";
import type { TenantContext } from "../context/tenant-context";

// ============================================================================
// Types
// ============================================================================

/** Property definition for tool input schema */
export interface ToolProperty {
  type: string;
  description: string;
  enum?: string[];
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  items?: unknown;
  properties?: Record<string, ToolProperty>;
  additionalProperties?: boolean;
  required?: string[];
}

/** Input schema definition for a tool */
export interface ToolInputSchema {
  /** JSON Schema type (object for structured inputs) */
  type: "object";

  /** Required field names */
  required: string[];

  /** Property definitions with descriptions for LLM */
  properties: Record<string, ToolProperty>;

  /** Additional properties not allowed per §2.4 (max 5-8 top-level params) */
  additionalProperties: false;
}

/** Tool metadata for registry */
export interface ToolMetadata {
  /** Tool name - unique identifier */
  name: string;

  /**
   * Tool description for LLM selection.
   *
   * CONTRACT.md §2.4:
   * - Minimum 50 characters
   * - Must include: when to use, when NOT to use, example
   * - Poor descriptions are #1 cause of tool misuse
   */
  description: string;

  /** Input JSON Schema with descriptions on every field */
  input_schema: ToolInputSchema;

  /** Required permission scopes to invoke this tool */
  required_permissions: string[];

  /** Whether tool is tenant-scoped (true for most tools) */
  tenant_scoped: boolean;

  /** Tool version for tracking changes */
  version: string;

  /** Timeout in milliseconds */
  timeout_ms: number;

  /** Whether tool supports partial success */
  supports_partial: boolean;
}

/** Registered tool with implementation */
export interface RegisteredTool<TInput, TOutput> extends ToolMetadata {
  /** The tool implementation function */
  implementation: (input: TInput, context: ToolExecutionContext) => Promise<ToolResult<TOutput>>;
}

/** Context provided during tool execution */
export interface ToolExecutionContext {
  /** Current tenant context (null for global tools) */
  tenant_context: TenantContext | null;

  /** Tool call trace ID for observability */
  trace_id: string;

  /** Tool call span ID for OpenTelemetry */
  span_id: string;

  /** Tool version being executed */
  tool_version: string;

  /** Start time for latency calculation */
  start_time_ms: number;
}

/** Framework binding types */
export type FrameworkType = "langchain" | "crewai" | "mcp" | "openai";

// ============================================================================
// Registry Class
// ============================================================================

/**
 * Central registry for all tools in the system.
 *
 * CONTRACT.md §2.4:
 * - Single discovery point for all tools
 * - Enables validation, permission checking, observability in one location
 * - Framework bindings auto-generated from canonical definitions
 */
export class ToolRegistry {
  private tools = new Map<string, RegisteredTool<unknown, unknown>>();
  private bindings = new Map<string, Map<FrameworkType, unknown>>();

  /**
   * Register a new tool in the registry.
   *
   * CONTRACT.md §2.4:
   * - All tools must be registered here
   * - Framework bindings auto-generated after registration
   * - Validation ensures schema compliance
   *
   * @param tool The tool to register
   *
   * @example
   * ```typescript
   * registry.register({
   *   name: "create_invoice",
   *   description: "Creates a new invoice...",
   *   input_schema: { ... },
   *   required_permissions: ["billing:write"],
   *   tenant_scoped: true,
   *   version: "1.0.0",
   *   timeout_ms: 30000,
   *   supports_partial: false,
   *   implementation: async (input, ctx) => { ... }
   * });
   * ```
   */
  register<TInput, TOutput>(tool: RegisteredTool<TInput, TOutput>): void {
    // Validate tool metadata
    this.validateTool(tool);

    // Check for duplicates
    if (this.tools.has(tool.name)) {
      throw new Error(`Tool "${tool.name}" is already registered`);
    }

    // Store the tool
    this.tools.set(tool.name, tool as RegisteredTool<unknown, unknown>);

    // Auto-generate framework bindings
    this.generateBindings(tool);

    console.log(`[ToolRegistry] Registered: ${tool.name} v${tool.version}`);
  }

  /**
   * Get a tool by name.
   *
   * @param name Tool name
   * @returns The registered tool or undefined
   */
  get<TInput = unknown, TOutput = unknown>(
    name: string
  ): RegisteredTool<TInput, TOutput> | undefined {
    return this.tools.get(name) as RegisteredTool<TInput, TOutput> | undefined;
  }

  /**
   * Check if a tool exists in the registry.
   */
  has(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * List all registered tools.
   */
  list(): ToolMetadata[] {
    return Array.from(this.tools.values()).map((tool) => ({
      name: tool.name,
      description: tool.description,
      input_schema: tool.input_schema,
      required_permissions: tool.required_permissions,
      tenant_scoped: tool.tenant_scoped,
      version: tool.version,
      timeout_ms: tool.timeout_ms,
      supports_partial: tool.supports_partial,
    }));
  }

  /**
   * Get framework-specific binding for a tool.
   *
   * CONTRACT.md §2.4:
   * - Framework bindings are auto-generated
   * - Maximum 10 lines, no business logic
   * - Pure translation layer
   */
  getBinding(name: string, framework: FrameworkType): unknown {
    const frameworkBindings = this.bindings.get(name);
    if (!frameworkBindings) {
      throw new Error(`Tool "${name}" not found`);
    }

    const binding = frameworkBindings.get(framework);
    if (!binding) {
      throw new Error(`No ${framework} binding for tool "${name}"`);
    }

    return binding;
  }

  /**
   * Validate that all tools have bindings for all supported frameworks.
   *
   * CONTRACT.md §2.4:
   * - CI gate validates binding parity
   * - Build fails if any tool is missing bindings
   */
  validateBindingParity(): string[] {
    const errors: string[] = [];
    const supportedFrameworks: FrameworkType[] = ["langchain", "crewai", "mcp", "openai"];

    for (const [name, tool] of this.tools) {
      const frameworkBindings = this.bindings.get(name);

      for (const framework of supportedFrameworks) {
        if (!frameworkBindings?.has(framework)) {
          errors.push(`Tool "${name}" missing ${framework} binding`);
        }
      }
    }

    return errors;
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private validateTool(tool: RegisteredTool<unknown, unknown>): void {
    // CONTRACT.md §2.4: Description minimum 50 characters
    if (tool.description.length < 50) {
      throw new Error(
        `Tool "${tool.name}" description too short (${tool.description.length} chars, ` +
          `minimum 50). See CONTRACT.md §2.4 for description requirements.`
      );
    }

    // CONTRACT.md §2.4: Max 5-8 top-level parameters
    const paramCount = Object.keys(tool.input_schema.properties).length;
    if (paramCount > 8) {
      throw new Error(
        `Tool "${tool.name}" has too many parameters (${paramCount}, maximum 8). ` +
          `See CONTRACT.md §2.4 for schema constraints.`
      );
    }

    // Validate all properties have descriptions
    for (const [propName, prop] of Object.entries(tool.input_schema.properties)) {
      if (!prop.description || prop.description.length < 10) {
        throw new Error(
          `Tool "${tool.name}" property "${propName}" missing or too short description. ` +
            `See CONTRACT.md §2.4 for schema requirements.`
        );
      }
    }

    // Validate required fields
    if (!tool.input_schema.required) {
      throw new Error(`Tool "${tool.name}" must specify required fields`);
    }

    // Validate additionalProperties is false
    if (tool.input_schema.additionalProperties !== false) {
      throw new Error(
        `Tool "${tool.name}" must set additionalProperties: false. ` + `See CONTRACT.md §2.4.`
      );
    }
  }

  private generateBindings<TInput, TOutput>(
    tool: RegisteredTool<TInput, TOutput>
  ): void {
    const frameworkBindings = new Map<FrameworkType, unknown>();

    // LangChain binding - thin wrapper, max 10 lines
    frameworkBindings.set("langchain", {
      name: tool.name,
      description: tool.description,
      schema: tool.input_schema,
      func: async (input: TInput) => {
        // Implementation delegates to canonical tool
        return tool.implementation(input, this.createExecutionContext(tool));
      },
    });

    // CrewAI binding
    frameworkBindings.set("crewai", {
      name: tool.name,
      description: tool.description,
      func: async (input: TInput) => {
        return tool.implementation(input, this.createExecutionContext(tool));
      },
    });

    // MCP (Model Context Protocol) binding
    frameworkBindings.set("mcp", {
      name: tool.name,
      description: tool.description,
      inputSchema: tool.input_schema,
      handler: async (input: TInput) => {
        return tool.implementation(input, this.createExecutionContext(tool));
      },
    });

    // OpenAI function calling binding
    frameworkBindings.set("openai", {
      type: "function",
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.input_schema,
      },
      // Handler registered separately with OpenAI client
    });

    this.bindings.set(tool.name, frameworkBindings);
  }

  private createExecutionContext(tool: ToolMetadata): ToolExecutionContext {
    // Import here to avoid circular dependency
    const { getTenantContext } = require("../context/tenant-context");

    return {
      tenant_context: getTenantContext(),
      trace_id: generateTraceId(),
      span_id: generateSpanId(),
      tool_version: tool.version,
      start_time_ms: Date.now(),
    };
  }
}

// ============================================================================
// Utilities
// ============================================================================

function generateTraceId(): string {
  return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateSpanId(): string {
  return `span_${Math.random().toString(36).substr(2, 16)}`;
}

// ============================================================================
// Singleton Instance
// ============================================================================

/**
 * Global tool registry instance.
 *
 * All tools should be registered with this instance at application startup.
 * Framework bindings are auto-generated after registration.
 */
export const toolRegistry = new ToolRegistry();

// ============================================================================
// Helper for Tool Definition
// ============================================================================

/**
 * Helper to create a tool definition with type inference.
 *
 * @example
 * ```typescript
 * const createInvoiceTool = defineTool({
 *   name: "create_invoice",
 *   description: "Creates a new invoice...",
 *   input_schema: {
 *     type: "object",
 *     required: ["amount", "customer_id"],
 *     properties: {
 *       amount: { type: "number", description: "Invoice amount in cents" },
 *       customer_id: { type: "string", description: "Customer identifier" },
 *     },
 *     additionalProperties: false,
 *   },
 *   required_permissions: ["billing:write"],
 *   tenant_scoped: true,
 *   version: "1.0.0",
 *   timeout_ms: 30000,
 *   supports_partial: false,
 *   implementation: async (input, ctx) => {
 *     // Tool implementation
 *     return {
 *       status: "success",
 *       data: { invoice_id: "inv-123" },
 *       metadata: { ... }
 *     };
 *   },
 * });
 * ```
 */
export function defineTool<TInput, TOutput>(
  tool: RegisteredTool<TInput, TOutput>
): RegisteredTool<TInput, TOutput> {
  return tool;
}
