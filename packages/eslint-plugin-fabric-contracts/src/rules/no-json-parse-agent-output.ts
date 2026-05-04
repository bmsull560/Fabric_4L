/**
 * @fileoverview Rule to prevent JSON.parse() on LLM agent outputs
 *
 * CONTRACT.md §2.5 - LLM Output Handling
 * Anti-Pattern: JSON.parse() on LLM responses
 *
 * Agent outputs must use structured generation (Zod schemas), not ad-hoc parsing.
 * This ensures:
 * - Schema-validated responses at generation time
 * - No runtime parsing failures
 * - Type safety from LLM to application code
 *
 * @example
 * // Incorrect - JSON.parse on LLM output
 * const output = JSON.parse(llmResponse);
 *
 * // Correct - structured generation with Zod
 * const output = await agent.execute(input); // Already typed
 */

import { Rule } from "eslint";

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Disallow JSON.parse() on LLM/agent outputs - use structured generation",
      category: "Canonical Contracts",
      recommended: true,
      url: "https://github.com/bmsull560/Fabric_4L/blob/main/contract.md#25-llm-output-handling",
    },
    schema: [],
    messages: {
      noJsonParseAgentOutput:
        "JSON.parse() is not allowed on LLM/agent outputs. " +
        "Use structured generation with Zod schemas instead. " +
        "See contract.md §2.5 for canonical pattern.",
    },
  },

  create(context: Rule.RuleContext): Rule.RuleListener {
    /**
     * Check if the argument to JSON.parse looks like it comes from an LLM/agent
     * Heuristics: variable name contains "llm", "agent", "response", "output", "completion"
     */
    function isLLMOutput(node: any): boolean {
      const suspiciousPatterns = /llm|agent|response|output|completion|gpt|claude/i;

      // Check if argument is an identifier with suspicious name
      if (node.type === "Identifier" && suspiciousPatterns.test(node.name)) {
        return true;
      }

      // Check if argument is a member expression like agent.output, llm.response
      if (node.type === "MemberExpression") {
        const objName = node.object?.name || "";
        const propName = node.property?.name || "";
        if (suspiciousPatterns.test(objName) || suspiciousPatterns.test(propName)) {
          return true;
        }
      }

      return false;
    }

    return {
      // Detect JSON.parse() calls
      CallExpression(node: any): void {
        const callee = node.callee;

        // Check if it's JSON.parse
        if (
          callee.type === "MemberExpression" &&
          callee.object?.name === "JSON" &&
          callee.property?.name === "parse"
        ) {
          // Check if the argument looks like LLM output
          const arg = node.arguments[0];
          if (arg && isLLMOutput(arg)) {
            context.report({
              node,
              messageId: "noJsonParseAgentOutput",
            });
          }
        }
      },
    };
  },
};

export = rule;
