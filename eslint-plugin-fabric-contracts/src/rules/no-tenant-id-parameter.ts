/**
 * @fileoverview Rule to prevent tenantId as a function parameter
 *
 * CONTRACT.md §2.1 - Tenant Isolation Boundary
 * Anti-Pattern: Function parameters named tenantId, tenant_id, tenantID, etc.
 *
 * Tenant context must flow via AsyncLocalStorage (context/tenant-context.ts),
 * not through explicit parameters. This ensures:
 * - Automatic propagation through async call stacks
 * - No manual passing through deep call chains
 * - No risk of parameter mismatch or omission
 *
 * @example
 * // Incorrect - tenantId as parameter
 * function getUser(tenantId: string, userId: string) { ... }
 *
 * // Correct - tenant from context
 * function getUser(userId: string) {
 *   const tenantId = getCurrentTenant();
 *   ...
 * }
 */

import { Rule } from "eslint";

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description: "Disallow tenantId as function parameters - use AsyncLocalStorage context",
      category: "Canonical Contracts",
      recommended: true,
      url: "https://github.com/bmsull560/Fabric_4L/blob/main/contract.md#21-tenant-isolation-boundary",
    },
    schema: [],
    messages: {
      noTenantIdParameter:
        "{{parameterName}} is not allowed as a function parameter. " +
        "Tenant context must flow via AsyncLocalStorage (getCurrentTenant() from context/tenant-context.ts). " +
        "See contract.md §2.1 for canonical pattern.",
    },
  },

  create(context: Rule.RuleContext): Rule.RuleListener {
    // Pattern matching tenantId, tenant_id, tenantID, tenantIdParam, etc.
    const tenantIdPattern = /tenant[_-]?id/i;
    const sourceCode = context.getSourceCode();

    /**
     * Check if an identifier matches tenantId patterns
     */
    function isTenantIdParameter(name: string): boolean {
      return tenantIdPattern.test(name);
    }

    /**
     * Report violation for a parameter
     */
    function reportParameter(
      node: any,
      name: string
    ): void {
      context.report({
        node: node as any,
        messageId: "noTenantIdParameter",
        data: {
          parameterName: name,
        },
      });
    }

    /**
     * Extract parameter name and check for violations
     */
    function checkParameter(param: any): void {
      // Direct identifier: function foo(tenantId)
      if (param.type === "Identifier") {
        if (isTenantIdParameter(param.name)) {
          reportParameter(param, param.name);
        }
        return;
      }

      // Object destructuring: function foo({ tenantId })
      if (param.type === "ObjectPattern") {
        for (const prop of param.properties) {
          if (prop.type === "Property" && prop.key.type === "Identifier") {
            if (isTenantIdParameter(prop.key.name)) {
              reportParameter(prop.key, prop.key.name);
            }
          }
          // Handle nested destructuring: function foo({ user: { tenantId } })
          if (prop.type === "Property" && prop.value.type === "ObjectPattern") {
            checkParameter(prop.value);
          }
        }
        return;
      }

      // Array destructuring: function foo([tenantId])
      if (param.type === "ArrayPattern") {
        for (const element of param.elements) {
          if (element) {
            checkParameter(element);
          }
        }
        return;
      }

      // Rest element: function foo(...tenantIds)
      if (param.type === "RestElement") {
        if (param.argument.type === "Identifier" && isTenantIdParameter(param.argument.name)) {
          reportParameter(param.argument, param.argument.name);
        }
      }
    }

    return {
      // Check function declarations: function foo(tenantId) { ... }
      FunctionDeclaration(node: any): void {
        for (const param of node.params) {
          checkParameter(param as any);
        }
      },

      // Check function expressions: const foo = function(tenantId) { ... }
      FunctionExpression(node: any): void {
        for (const param of node.params) {
          checkParameter(param as any);
        }
      },

      // Check arrow functions: const foo = (tenantId) => { ... }
      ArrowFunctionExpression(node: any): void {
        for (const param of node.params) {
          checkParameter(param as any);
        }
      },

      // Check method definitions: class Foo { bar(tenantId) { ... } }
      MethodDefinition(node: any): void {
        if (node.value && node.value.params) {
          for (const param of node.value.params) {
            checkParameter(param as any);
          }
        }
      },
    };
  },
};

export = rule;
