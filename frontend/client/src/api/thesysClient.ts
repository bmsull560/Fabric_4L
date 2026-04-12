/**
 * Thesys C1 API Client
 * OpenAI-compatible API for Generative UI streaming
 */

import { apiClient } from './client';

const THESYS_API_KEY = import.meta.env.VITE_THESYS_API_KEY || '';
const THESYS_BASE_URL = import.meta.env.VITE_THESYS_BASE_URL || 'https://api.thesys.dev/v1/embed';
const ENABLE_C1 = import.meta.env.VITE_ENABLE_C1_REPORTS === 'true';

export interface C1Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface C1StreamChunk {
  type: 'content' | 'component' | 'error' | 'done';
  data?: unknown;
  error?: string;
}

export interface C1Component {
  type: string;
  props: Record<string, unknown>;
}

/**
 * Check if C1 integration is enabled and configured
 */
export function isC1Enabled(): boolean {
  return ENABLE_C1 && THESYS_API_KEY.length > 0;
}

/**
 * Stream C1 response for interactive UI generation
 * Uses server-side proxy to protect API key
 */
export async function* streamC1Response(
  messages: C1Message[],
  businessCaseId: string,
  businessCaseData?: Record<string, unknown>
): AsyncGenerator<C1StreamChunk, void, unknown> {
  if (!isC1Enabled()) {
    yield { type: 'error', error: 'C1 is not enabled. Check VITE_ENABLE_C1_REPORTS and VITE_THESYS_API_KEY.' };
    return;
  }

  try {
    // Use L4 proxy endpoint to hide API key from client
    const response = await apiClient.post('l4', '/c1/stream', {
      messages,
      business_case_id: businessCaseId,
      business_case_data: businessCaseData,
    }, {
      responseType: 'stream',
    });

    const reader = response.data.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(line => line.trim());

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6)) as C1StreamChunk;
            yield data;
          } catch {
            // Ignore malformed chunks
          }
        }
      }
    }

    yield { type: 'done' };
  } catch (error) {
    yield {
      type: 'error',
      error: error instanceof Error ? error.message : 'Failed to stream C1 response',
    };
  }
}

/**
 * Evaluate formula via Value Fabric API and return formatted result
 * Called by C1-generated components when sliders change
 */
export async function evaluateWhatIf(
  baseCaseId: string,
  adjustments: Array<{ name: string; value: number; original_value: number }>
): Promise<{
  original_value: number;
  adjusted_value: number;
  delta_percentage: number;
  new_roi: number;
  new_payback_months: number;
  formula_used: string;
}> {
  const response = await apiClient.post('l3', '/formulas/scenario', {
    base_case_id: baseCaseId,
    adjustments,
  });

  return response.data;
}

/**
 * Save scenario to localStorage (MVP implementation)
 * Can be upgraded to backend persistence later
 */
export function saveScenario(
  caseId: string,
  scenarioName: string,
  adjustments: Array<{ name: string; value: number }>
): string {
  const scenarioId = `scenario_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
  const scenarios = getScenarios(caseId);

  scenarios.push({
    id: scenarioId,
    name: scenarioName,
    adjustments,
    created_at: new Date().toISOString(),
  });

  localStorage.setItem(`vf_scenarios_${caseId}`, JSON.stringify(scenarios));
  return scenarioId;
}

/**
 * Get saved scenarios for a business case
 */
export interface SavedScenario {
  id: string;
  name: string;
  adjustments: Array<{ name: string; value: number }>;
  created_at: string;
}

export function getScenarios(caseId: string): SavedScenario[] {
  try {
    const stored = localStorage.getItem(`vf_scenarios_${caseId}`);
    if (!stored) return [];
    const parsed = JSON.parse(stored) as SavedScenario[];
    // Validate structure to prevent crashes from corrupt data
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    // Clear corrupt data
    localStorage.removeItem(`vf_scenarios_${caseId}`);
    return [];
  }
}

/**
 * Compare multiple scenarios
 */
export interface ScenarioComparison {
  id: string;
  name: string;
  adjustments: Array<{ name: string; value: number }>;
  created_at: string;
}

export function compareScenarios(
  caseId: string,
  scenarioIds: string[]
): ScenarioComparison[] {
  const allScenarios = getScenarios(caseId);
  return allScenarios.filter(s => scenarioIds.includes(s.id));
}

export { THESYS_API_KEY, THESYS_BASE_URL, ENABLE_C1 };
