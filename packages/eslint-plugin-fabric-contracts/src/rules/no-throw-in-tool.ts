/**
 * @fileoverview Rule to prevent throw statements in tool implementations
 *
 * CONTRACT.md §2.4 - Tool Invocation Boundary
 * Anti-Pattern: throw in tool implementations
 *
 * Tools must return {success, data, error} shapes via error-shape.ts helpers,
 * never throw. This ensures:
 * - Structured error responses for downstream handling
 * - No stack trace leakage to clients
 * - Consistent error contract across all tools
 *
 * @example
 * // Incorrect - throw in tool
 * function myTool() {
 *   if (invalid) throw new Error("Invalid input");
 * }
 *
 * // Correct - return error shape
 * function myTool() {
 *   if (invalid) return error("INVALID_INPUT", "Invalid input");
 *   return success({ result });
 * }
 */

import { Rule } from "eslint";

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Disallow throw statements in tool implementations - use error() helper",
      category: "Canonical Contracts",
      recommended: true,
      url: "https://github.com/bmsull560/Fabric_4L/blob/main/contract.md#24-tool-invocation-boundary",
    },
    schema: [],
    messages: {
      noThrowInTool:
        "throw is not allowed in tool implementations. " +
        "Use error() helper from errors/error-shape.ts instead. " +
        "See contract.md §2.4 for canonical pattern.",
    },
  },

  create(context: Rule.RuleContext): Rule.RuleListener {
    // Track if we're inside a tool function
    let toolFunctionDepth = 0;

    /**
     * Check if a function is a tool implementation
     * Heuristics: function name contains "tool" or is exported from tools/
     */
    function isToolFunction(node: any): boolean {
      // Check function name
      const name = node.id?.name || node.key?.name || "";
      if (/tool/i.test(name)) {
        return true;
      }

      // Check if parent is a tools export
      const parent = node.parent;
      if (parent?.type === "ExportNamedDeclaration") {
        return true;
      }

      return false;
    }

    return {
      // Track entry into tool functions
      FunctionDeclaration(node: any): void {
        if (isToolFunction(node)) {
          toolFunctionDepth++;
        }
      },
      "FunctionDeclaration:exit"(node: any): void {
        if (isToolFunction(node)) {
          toolFunctionDepth--;
        }
      },

      FunctionExpression(node: any): void {
        if (isToolFunction(node)) {
          toolFunctionDepth++;
        }
      },
      "FunctionExpression:exit"(node: any): void {
        if (isToolFunction(node)) {
          toolFunctionDepth--;
        }
      },

      ArrowFunctionExpression(node: any): void {
        if (isToolFunction(node)) {
          toolFunctionDepth++;
        }
      },
      "ArrowFunctionExpression:exit"(node: any): void {
        if (isToolFunction(node)) {
          toolFunctionDepth--;
        }
      },

      // Detect throw statements
      ThrowStatement(node: any): void {
        if (toolFunctionDepth > 0) {
          context.report({
            node,
            messageId: "noThrowInTool",
          });
        }
      },
    };
  },
};

export = rule;
