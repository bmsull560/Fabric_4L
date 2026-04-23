/**
 * @fileoverview Rule to prevent URL string concatenation
 *
 * CONTRACT.md §2.6 - UI State Management
 * Anti-Pattern: URL string concatenation: "/path/" + id
 *
 * URL construction must be centralized via the route manifest, not ad-hoc concatenation.
 * This ensures:
 * - All routes are defined in the manifest
 * - No broken links from string concatenation errors
 * - Type-safe route parameters
 */

import { Rule } from "eslint";

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Disallow URL string concatenation - use route manifest",
      category: "Canonical Contracts",
      recommended: true,
      url: "https://github.com/bmsull560/Fabric_4L/blob/main/contract.md#26-ui-state-management",
    },
    schema: [],
    messages: {
      noUrlConcatenation:
        "URL string concatenation is not allowed. " +
        "Use the route manifest for URL construction. " +
        "See contract.md §2.6 for canonical pattern.",
    },
  },

  create(context: Rule.RuleContext): Rule.RuleListener {
    return {
      // Detect string concatenation with "/"
      BinaryExpression(node: any): void {
        if (node.operator === "+") {
          const left = context.getSourceCode().getText(node.left);
          const right = context.getSourceCode().getText(node.right);

          // Check if either side looks like a URL/path
          if (
            left.includes("/") ||
            right.includes("/") ||
            /['"]\//.test(left) ||
            /['"]\//.test(right)
          ) {
            context.report({
              node,
              messageId: "noUrlConcatenation",
            });
          }
        }
      },
    };
  },
};

export = rule;
