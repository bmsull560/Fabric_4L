import { Rule } from "eslint";
import { TSESTree } from "@typescript-eslint/types";

export type RuleContext = Rule.RuleContext;
export type RuleListener = Rule.RuleListener;

export type FunctionLikeNode =
  | TSESTree.FunctionDeclaration
  | TSESTree.FunctionExpression
  | TSESTree.ArrowFunctionExpression;

export type ParameterNode = TSESTree.Parameter;

export function asTSNode<T extends TSESTree.Node>(node: unknown): T {
  return node as T;
}

export { TSESTree };
