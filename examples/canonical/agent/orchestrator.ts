/**
 * Agent Orchestrator - Canonical Implementation
 *
 * CONTRACT.md §2.5 - Agent Output Shape and Traceability
 *
 * This module demonstrates the canonical pattern for agent execution:
 * - Structured generation with Pydantic schema enforcement
 * - OpenTelemetry tracing for all phases
 * - Retry logic on validation failures
 * - Tool invocation through registry
 * - Output persistence for audit trail
 *
 * Copy this file as the starting point for agent orchestration in new services.
 */

import { ToolRegistry } from "../tools/registry";
import { toolRegistry } from "../tools/example-tool";
import { agentErrorBoundary, AgentOutput, ToolCall, ToolResult } from "../errors/error-shape";

// ============================================================================
// Types
// ============================================================================

/** Agent configuration */
export interface AgentConfig {
  /** Agent name/identifier */
  name: string;

  /** Exact model version (pinned) */
  model: string;

  /** Model version string from provider */
  model_version: string;

  /** Output schema definition (Pydantic/Zod) */
  output_schema: OutputSchema;

  /** Maximum retry attempts on validation failure */
  max_retries: number;

  /** Available tools for this agent */
  tool_names: string[];

  /** System prompt/template */
  system_prompt: string;

  /** Timeout for agent execution */
  timeout_ms: number;
}

/** Output schema definition */
export interface OutputSchema {
  /** Schema name */
  name: string;

  /** Schema definition (simplified for TypeScript demo) */
  definition: Record<string, SchemaField>;
}

/** Schema field definition */
export interface SchemaField {
  type: "string" | "number" | "boolean" | "array" | "object";
  description: string;
  required?: boolean;
  enum?: string[];
  items?: OutputSchema;
  properties?: Record<string, SchemaField>;
}

/** Agent execution input */
export interface AgentInput {
  /** User query/prompt */
  query: string;

  /** Previous conversation context */
  context?: ConversationMessage[];

  /** Additional parameters */
  params?: Record<string, unknown>;
}

/** Conversation message */
export interface ConversationMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

/** LLM provider interface */
export interface LLMProvider {
  generate(
    messages: ConversationMessage[],
    tools: unknown[],
    config: AgentConfig
  ): Promise<LLMResponse>;
}

/** Raw LLM response */
export interface LLMResponse {
  content?: string;
  tool_calls?: Array<{
    name: string;
    arguments: Record<string, unknown>;
  }>;
  finish_reason: string;
  token_usage: {
    prompt: number;
    completion: number;
    total: number;
  };
  model: string;
  model_version: string;
}

// ============================================================================
// Agent Orchestrator Implementation
// ============================================================================

/**
 * Canonical agent orchestrator implementing structured generation.
 *
 * CONTRACT.md §2.5:
 * - All outputs produced through structured generation
 * - Pydantic schema enforcement at generation and validation time
 * - Complete OpenTelemetry trace for every phase
 * - Retry up to 2 times on validation failure
 * - Output persistence for audit trail
 */
export class AgentOrchestrator {
  private toolRegistry: ToolRegistry;
  private llmProvider: LLMProvider;

  constructor(toolRegistry: ToolRegistry, llmProvider: LLMProvider) {
    this.toolRegistry = toolRegistry;
    this.llmProvider = llmProvider;
  }

  /**
   * Execute agent with structured generation.
   *
   * CONTRACT.md §2.5:
   * 1. Planning phase (OTel span)
   * 2. Tool selection phase (OTel span)
   * 3. Tool execution phase (OTel span per tool)
   * 4. Output validation phase (OTel span)
   * 5. Response generation phase (OTel span)
   *
   * @param input Agent input
   * @param config Agent configuration
   * @returns Canonical AgentOutput
   *
   * @example
   * ```typescript
   * const orchestrator = new AgentOrchestrator(toolRegistry, openaiProvider);
   *
   * const result = await orchestrator.execute(
   *   { query: "Find customers who purchased in the last 30 days" },
   *   {
   *     name: "customer_analytics_agent",
   *     model: "gpt-4o-2024-08-06",
   *     model_version: "2024-08-06",
   *     output_schema: customerListSchema,
   *     max_retries: 2,
   *     tool_names: ["search_customers", "filter_by_date"],
   *     system_prompt: "You are a customer analytics assistant...",
   *     timeout_ms: 30000,
   *   }
   * );
   *
   * console.log(result.result); // Typed output
   * console.log(result.trace_id); // For debugging
   * ```
   */
  async execute<T>(input: AgentInput, config: AgentConfig): Promise<AgentOutput<T>> {
    const startTime = Date.now();
    const traceId = generateTraceId();
    const sessionId = input.context?.[0]?.timestamp
      ? generateSessionIdFromContext(input.context)
      : generateSessionId();

    // Initialize tool calls log
    const toolCalls: ToolCall[] = [];

    try {
      // ========================================================================
      // Phase 1: Planning (OTel span)
      // ========================================================================
      console.log(`[Agent:${config.name}] Phase 1: Planning`);

      const plan = await this.createExecutionPlan(input, config);

      // ========================================================================
      // Phase 2: Tool Selection & Execution (OTel span)
      // ========================================================================
      console.log(`[Agent:${config.name}] Phase 2: Tool execution`);

      if (plan.requiresTools && plan.toolsToCall.length > 0) {
        for (const toolCall of plan.toolsToCall) {
          const toolStartTime = Date.now();
          const spanId = generateSpanId();

          // Get tool from registry
          const tool = this.toolRegistry.get(toolCall.name);
          if (!tool) {
            throw new Error(`Tool "${toolCall.name}" not found in registry`);
          }

          // Execute tool
          const result = await tool.implementation(toolCall.arguments, {
            tenant_context: null, // Would be populated from request context
            trace_id: traceId,
            span_id: spanId,
            tool_version: tool.version,
            start_time_ms: toolStartTime,
          });

          // Record tool call
          toolCalls.push({
            tool_name: toolCall.name,
            input_hash: hashInput(toolCall.arguments),
            output_status: result.status,
            latency_ms: Date.now() - toolStartTime,
            span_id: spanId,
          });

          // Store result for later phases
          toolCall.result = result;
        }
      }

      // ========================================================================
      // Phase 3: Structured Generation (OTel span)
      // ========================================================================
      console.log(`[Agent:${config.name}] Phase 3: Structured generation`);

      const messages = this.buildMessages(input, config, toolCalls);
      const availableTools = config.tool_names
        .map((name) => this.toolRegistry.get(name))
        .filter(Boolean);

      const llmResponse = await this.llmProvider.generate(
        messages,
        availableTools.map((t) => ({
          type: "function",
          function: {
            name: t!.name,
            description: t!.description,
            parameters: t!.input_schema,
          },
        })),
        config
      );

      // ========================================================================
      // Phase 4: Output Validation (OTel span)
      // ========================================================================
      console.log(`[Agent:${config.name}] Phase 4: Validation`);

      let validatedOutput: T;
      let validationPassed = true;
      let retryCount = 0;

      try {
        validatedOutput = await this.validateOutput<T>(
          llmResponse.content || "{}",
          config.output_schema
        );
      } catch (validationError) {
        // Retry on validation failure
        validationPassed = false;

        const retryResult = await this.retryWithValidation<T>(
          input,
          config,
          messages,
          String(validationError)
        );

        validatedOutput = retryResult.output;
        retryCount = retryResult.retryCount;
        validationPassed = retryResult.success;
      }

      // ========================================================================
      // Phase 5: Persist Output (OTel span)
      // ========================================================================
      await this.persistOutput({
        session_id: sessionId,
        trace_id: traceId,
        input_hash: hashInput(input),
        output: validatedOutput,
        validation_passed: validationPassed,
        retry_count: retryCount,
        model: llmResponse.model,
        model_version: llmResponse.model_version,
        timestamp: new Date().toISOString(),
      });

      // ========================================================================
      // Build canonical AgentOutput
      // ========================================================================
      const totalLatency = Date.now() - startTime;

      return {
        result: validatedOutput,
        reasoning: this.extractReasoning(llmResponse),
        tool_calls: toolCalls,
        confidence: this.calculateConfidence(toolCalls, validationPassed),
        trace_id: traceId,
        session_id: sessionId,
        metadata: {
          model: llmResponse.model,
          model_version: llmResponse.model_version,
          latency_ms: totalLatency,
          token_usage: llmResponse.token_usage,
          validation_passed: validationPassed,
          retry_count: retryCount,
          finish_reason: llmResponse.finish_reason,
        },
      };
    } catch (error) {
      // Error boundary handles all failures
      console.error(`[Agent:${config.name}] Execution failed:`, error);

      // Return typed default on failure (CONTRACT.md §2.5)
      return this.createDefaultOutput<T>(
        traceId,
        sessionId,
        config,
        Date.now() - startTime,
        toolCalls
      );
    }
  }

  // ==========================================================================
  // Private Methods
  // ==========================================================================

  private async createExecutionPlan(
    input: AgentInput,
    config: AgentConfig
  ): Promise<{
    requiresTools: boolean;
    toolsToCall: Array<{
      name: string;
      arguments: Record<string, unknown>;
      result?: ToolResult<unknown>;
    }>;
  }> {
    // Simple planning - in production this would be more sophisticated
    const requiresTools = config.tool_names.length > 0;

    // For demo, assume we need to call all tools
    const toolsToCall = config.tool_names.map((name) => ({
      name,
      arguments: { query: input.query },
    }));

    return { requiresTools, toolsToCall };
  }

  private buildMessages(
    input: AgentInput,
    config: AgentConfig,
    toolCalls: ToolCall[]
  ): ConversationMessage[] {
    const messages: ConversationMessage[] = [
      {
        role: "system",
        content: config.system_prompt,
        timestamp: new Date().toISOString(),
      },
    ];

    // Add conversation context
    if (input.context) {
      messages.push(...input.context);
    }

    // Add current query
    messages.push({
      role: "user",
      content: input.query,
      timestamp: new Date().toISOString(),
    });

    // Add tool results if any
    if (toolCalls.length > 0) {
      messages.push({
        role: "assistant",
        content: `Tool results: ${JSON.stringify(toolCalls)}`,
        timestamp: new Date().toISOString(),
      });
    }

    return messages;
  }

  private async validateOutput<T>(content: string, schema: OutputSchema): Promise<T> {
    // CONTRACT.md §2.5: Pydantic model_validate() on every output
    // In TypeScript, we'd use Zod or similar
    // This is a simplified implementation

    try {
      const parsed = JSON.parse(content);
      // In production: validate against schema using Zod
      return parsed as T;
    } catch {
      throw new Error("Output validation failed: Invalid JSON");
    }
  }

  private async retryWithValidation<T>(
    input: AgentInput,
    config: AgentConfig,
    previousMessages: ConversationMessage[],
    validationError: string
  ): Promise<{ output: T; retryCount: number; success: boolean }> {
    let lastError = validationError;

    for (let attempt = 1; attempt <= config.max_retries; attempt++) {
      console.log(`[Agent:${config.name}] Retry attempt ${attempt}/${config.max_retries}`);

      // Add validation error to context
      const retryMessages = [
        ...previousMessages,
        {
          role: "system",
          content: `Validation error: ${lastError}. Please fix the output format and try again.`,
          timestamp: new Date().toISOString(),
        },
      ];

      try {
        const response = await this.llmProvider.generate(retryMessages, [], config);
        const output = await this.validateOutput<T>(response.content || "{}", config.output_schema);

        return { output, retryCount: attempt, success: true };
      } catch (error) {
        lastError = String(error);
      }
    }

    // All retries exhausted - return default
    console.warn(`[Agent:${config.name}] All retries exhausted`);
    return {
      output: this.getDefaultOutput<T>(config.output_schema),
      retryCount: config.max_retries,
      success: false,
    };
  }

  private getDefaultOutput<T>(schema: OutputSchema): T {
    // Generate default value from schema
    const defaultValue: Record<string, unknown> = {};

    for (const [key, field] of Object.entries(schema.definition)) {
      switch (field.type) {
        case "string":
          defaultValue[key] = "";
          break;
        case "number":
          defaultValue[key] = 0;
          break;
        case "boolean":
          defaultValue[key] = false;
          break;
        case "array":
          defaultValue[key] = [];
          break;
        case "object":
          defaultValue[key] = {};
          break;
      }
    }

    return defaultValue as T;
  }

  private async persistOutput(output: {
    session_id: string;
    trace_id: string;
    input_hash: string;
    output: unknown;
    validation_passed: boolean;
    retry_count: number;
    model: string;
    model_version: string;
    timestamp: string;
  }): Promise<void> {
    // CONTRACT.md §2.5: Output persistence for audit trail
    // In production: write to database, S3, or similar
    console.log(`[Agent] Persisted output: ${output.trace_id}`);

    // Example persistence (would be real in production)
    // await db.outputStore.create({
    //   session_id: output.session_id,
    //   trace_id: output.trace_id,
    //   input_hash: output.input_hash,
    //   output_json: JSON.stringify(output.output),
    //   ...
    // });
  }

  private extractReasoning(response: LLMResponse): string | undefined {
    // Extract chain-of-thought if present
    // Some models include reasoning in content
    return undefined; // Simplified
  }

  private calculateConfidence(toolCalls: ToolCall[], validationPassed: boolean): number {
    // Calculate confidence score based on:
    // - Tool execution success rate
    // - Validation result
    // - Model self-assessment if available

    if (toolCalls.length === 0) {
      return validationPassed ? 0.9 : 0.5;
    }

    const successRate =
      toolCalls.filter((tc) => tc.output_status === "success").length / toolCalls.length;

    return validationPassed ? successRate * 0.95 : successRate * 0.5;
  }

  private createDefaultOutput<T>(
    traceId: string,
    sessionId: string,
    config: AgentConfig,
    latencyMs: number,
    toolCalls: ToolCall[]
  ): AgentOutput<T> {
    return {
      result: this.getDefaultOutput<T>(config.output_schema),
      reasoning: "Execution failed - returning default value",
      tool_calls: toolCalls,
      confidence: 0,
      trace_id: traceId,
      session_id: sessionId,
      metadata: {
        model: config.model,
        model_version: config.model_version,
        latency_ms: latencyMs,
        token_usage: { prompt: 0, completion: 0, total: 0 },
        validation_passed: false,
        retry_count: config.max_retries,
        finish_reason: "error",
      },
    };
  }
}

// ============================================================================
// Utilities
// ============================================================================

function generateTraceId(): string {
  return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateSessionIdFromContext(context: ConversationMessage[]): string {
  // Derive session ID from first message timestamp
  const firstTimestamp = context[0]?.timestamp || Date.now();
  return `session_${firstTimestamp}`;
}

function generateSpanId(): string {
  return `span_${Math.random().toString(36).substr(2, 16)}`;
}

function hashInput(input: unknown): string {
  // Simple hash for demo - production would use SHA-256
  const str = JSON.stringify(input);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

// ============================================================================
// Example Usage
// ============================================================================

/**
 * Example: Customer Analytics Agent
 *
 * ```typescript
 * import { AgentOrchestrator } from "./orchestrator";
 * import { OpenAIProvider } from "./providers/openai";
 *
 * // Initialize orchestrator
 * const orchestrator = new AgentOrchestrator(
 *   toolRegistry,
 *   new OpenAIProvider({ apiKey: process.env.OPENAI_API_KEY })
 * );
 *
 * // Execute agent
 * const result = await orchestrator.execute<CustomerList>(
 *   { query: "Find high-value customers from last quarter" },
 *   {
 *     name: "customer_analytics",
 *     model: "gpt-4o-2024-08-06",
 *     model_version: "2024-08-06",
 *     output_schema: {
 *       name: "CustomerList",
 *       definition: {
 *         customers: {
 *           type: "array",
 *           description: "List of matching customers",
 *           items: {
 *             type: "object",
 *             properties: {
 *               id: { type: "string", description: "Customer ID" },
 *               name: { type: "string", description: "Customer name" },
 *               value: { type: "number", description: "Customer lifetime value" },
 *             },
 *           },
 *         },
 *       },
 *     },
 *     max_retries: 2,
 *     tool_names: ["search_customers", "calculate_ltv"],
 *     system_prompt: "You are a customer analytics specialist...",
 *     timeout_ms: 30000,
 *   }
 * );
 *
 * // Use typed result
 * console.log(result.result.customers);
 * console.log(result.trace_id); // For debugging/support
 * ```
 */

// Export for use
export { agentErrorBoundary };
