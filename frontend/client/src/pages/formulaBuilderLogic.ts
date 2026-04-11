/**
 * Formula Builder Logic - Extracted for testability
 * Contains pure functions for validation, state transitions, and calculations
 */

export type ActivationState = "draft" | "pending" | "approved";
export type VariableType = "rate" | "currency" | "integer" | "percent" | "decimal";
export type SourceType = "CRM" | "Billing" | "Model" | "Manual" | "ERP";

export interface FormulaVariable {
  name: string;
  type: VariableType;
  source: SourceType;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface StatusConfig {
  label: string;
  color: string;
  icon: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Validation Rules
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Validates a formula expression for syntax and variable references
 */
export function validateFormulaExpression(
  expression: string,
  availableVariables: FormulaVariable[]
): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check for empty expression
  if (!expression || expression.trim() === "") {
    errors.push("Formula expression is required");
    return { valid: false, errors, warnings };
  }

  // Check for balanced brackets
  const openBrackets = (expression.match(/\{/g) || []).length;
  const closeBrackets = (expression.match(/\}/g) || []).length;
  if (openBrackets !== closeBrackets) {
    errors.push(`Unbalanced brackets: ${openBrackets} opening, ${closeBrackets} closing`);
  }

  // Extract variable references (capture content inside brackets)
  const variableRefs = expression.match(/\{([^}]*)\}/g) || [];
  const referencedVarNames = variableRefs
    .filter((ref) => ref !== "{}") // Exclude empty refs
    .map((ref) => ref.slice(1, -1));

  // Check for empty variable references
  const hasEmptyRef = variableRefs.some((ref) => ref === "{}");
  if (hasEmptyRef) {
    errors.push("Empty variable reference found: {}");
  }

  // Check for undefined variables
  const availableNames = availableVariables.map((v) => v.name);
  const undefinedVars = referencedVarNames.filter(
    (name) => !availableNames.includes(name)
  );
  if (undefinedVars.length > 0) {
    errors.push(`Undefined variables: ${undefinedVars.join(", ")}`);
  }

  // Check for unused variables (warning)
  const usedVars = new Set(referencedVarNames);
  const unusedVars = availableVariables.filter((v) => !usedVars.has(v.name));
  if (unusedVars.length > 0) {
    warnings.push(
      `Unused variables: ${unusedVars.map((v) => v.name).join(", ")}`
    );
  }

  // Check for valid operators
  const validOperators = ["+", "-", "*", "/", "(", ")", "^", "%"];
  const placeholder = "VAR";
  // Replace all variable references (including empty {}) with placeholder
  const sanitizedExpr = expression
    .replace(/\{[^}]*\}/g, placeholder)
    .replace(/[\d\s.]/g, ""); // Remove numbers and whitespace

  // Remove all placeholder occurrences before checking for invalid chars
  const withoutPlaceholders = sanitizedExpr.replace(new RegExp(placeholder, "g"), "");
  const invalidChars = withoutPlaceholders
    .split("")
    .filter((char) => !validOperators.includes(char));

  if (invalidChars.length > 0) {
    const uniqueInvalid = Array.from(new Set(invalidChars));
    errors.push(`Invalid characters: ${uniqueInvalid.join(", ")}`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Validates that all required variables are bound
 */
export function validateVariableBindings(
  requiredVars: string[],
  boundVars: FormulaVariable[]
): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  const boundNames = boundVars.map((v) => v.name);
  const missing = requiredVars.filter((name) => !boundNames.includes(name));

  if (missing.length > 0) {
    errors.push(`Missing required variables: ${missing.join(", ")}`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// State Transitions
// ─────────────────────────────────────────────────────────────────────────────

/**
 * State machine for formula activation workflow
 */
export const ACTIVATION_TRANSITIONS: Record<
  ActivationState,
  ActivationState[]
> = {
  draft: ["pending"],
  pending: ["approved", "draft"],
  approved: ["draft"], // Revise goes back to draft
};

/**
 * Checks if a state transition is valid
 */
export function canTransitionState(
  from: ActivationState,
  to: ActivationState
): boolean {
  return ACTIVATION_TRANSITIONS[from].includes(to);
}

/**
 * Gets available next states from current state
 */
export function getAvailableTransitions(
  current: ActivationState
): ActivationState[] {
  return ACTIVATION_TRANSITIONS[current];
}

/**
 * Gets the action label for a state transition
 */
export function getTransitionAction(
  from: ActivationState,
  to: ActivationState
): string | null {
  const transitions: Record<string, string> = {
    "draft->pending": "Submit for Approval",
    "pending->approved": "Approve",
    "pending->draft": "Reject",
    "approved->draft": "Revise",
  };
  return transitions[`${from}->${to}`] || null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Derived Values / Calculations
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Status label configuration based on activation state
 */
export function getStatusConfig(state: ActivationState): StatusConfig {
  const configs: Record<ActivationState, StatusConfig> = {
    draft: {
      label: "Draft",
      color: "bg-neutral-100 text-neutral-600",
      icon: "clock",
    },
    pending: {
      label: "Pending Approval",
      color: "bg-amber-50 text-amber-700",
      icon: "alert-circle",
    },
    approved: {
      label: "Active",
      color: "bg-emerald-50 text-emerald-700",
      icon: "check-circle",
    },
  };
  return configs[state];
}

/**
 * Color mapping for variable source types
 */
export function getSourceTypeColor(source: SourceType): string {
  const colors: Record<SourceType, string> = {
    CRM: "bg-blue-50 text-blue-700",
    Billing: "bg-emerald-50 text-emerald-700",
    Model: "bg-violet-50 text-violet-700",
    Manual: "bg-amber-50 text-amber-700",
    ERP: "bg-cyan-50 text-cyan-700",
  };
  return colors[source] || "bg-neutral-50 text-neutral-600";
}

/**
 * Color mapping for variable types
 */
export function getVariableTypeColor(type: VariableType): string {
  const colors: Record<VariableType, string> = {
    rate: "bg-cyan-100 text-cyan-700",
    currency: "bg-emerald-100 text-emerald-700",
    integer: "bg-neutral-100 text-neutral-600",
    percent: "bg-purple-100 text-purple-700",
    decimal: "bg-orange-100 text-orange-700",
  };
  return colors[type] || "bg-neutral-100 text-neutral-600";
}

/**
 * Calculates ROI from test inputs
 */
export function calculateROI(
  result: number,
  investment: number
): { roi: number; roiPercent: number } {
  if (investment <= 0) {
    return { roi: 0, roiPercent: 0 };
  }
  const roi = result - investment;
  const roiPercent = (roi / investment) * 100;
  return {
    roi,
    roiPercent: Math.round(roiPercent),
  };
}

/**
 * Parses numeric value from formatted string (e.g., "$100,000" → 100000)
 */
export function parseNumericValue(value: string): number {
  const cleaned = value.replace(/[$,%\s]/g, "");
  const numeric = parseFloat(cleaned);
  return isNaN(numeric) ? 0 : numeric;
}

// ─────────────────────────────────────────────────────────────────────────────
// Payload Shaping
// ─────────────────────────────────────────────────────────────────────────────

export interface FormulaPayload {
  name: string;
  description: string;
  expression: string;
  variables: FormulaVariable[];
  state: ActivationState;
  version: number;
  metadata: {
    createdAt: string;
    modifiedAt: string;
    author: string;
  };
}

/**
 * Builds the submission payload for saving a formula
 */
export function buildFormulaPayload(
  name: string,
  description: string,
  expression: string,
  variables: FormulaVariable[],
  state: ActivationState,
  version: number,
  author: string
): FormulaPayload {
  const now = new Date().toISOString();

  return {
    name,
    description,
    expression,
    variables,
    state,
    version,
    metadata: {
      createdAt: now, // In real app, this would come from existing record
      modifiedAt: now,
      author,
    },
  };
}

/**
 * Shapes the payload for version history entry
 */
export function buildVersionHistoryEntry(
  version: number,
  status: ActivationState,
  author: string,
  note: string
) {
  return {
    version: `v${version}`,
    status,
    author,
    date: new Date().toISOString(),
    note,
  };
}
