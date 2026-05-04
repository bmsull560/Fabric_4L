/**
 * Narrative Creation Store — UI state for the Value Narrative Hero
 *
 * Manages:
 * - Free-text input (company URL, CRM URL, earnings report, or description)
 * - Selected output type (narrative, roi_model, value_template)
 * - Selected industry for benchmark context
 * - Active input method (text, import, file, crm)
 */

import { create } from 'zustand';

export type OutputType = 'narrative' | 'roi_model' | 'value_template';
export type InputMethod = 'text' | 'import' | 'file' | 'crm';

/** Default industry when L6 industries are unavailable */
export const DEFAULT_INDUSTRY = 'Auto';

/** Fallback industries when L6 benchmark service is unreachable */
export const FALLBACK_INDUSTRIES = [
  'Auto', 'Software', 'Manufacturing', 'Financial Services',
  'Healthcare', 'Life Sciences', 'Retail', 'Energy',
];

/** Returns true if the input looks like a URL (http(s) or bare domain) */
export function looksLikeUrl(input: string): boolean {
  const trimmed = input.trim();
  return /^https?:\/\//i.test(trimmed) || /^[a-z0-9-]+\.[a-z]{2,}/i.test(trimmed);
}

export interface NarrativeStore {
  /** Free-text input from the hero textarea */
  prompt: string;
  setPrompt: (value: string) => void;

  /** Selected output type */
  outputType: OutputType;
  setOutputType: (type: OutputType) => void;

  /** Selected industry for benchmark context */
  industry: string;
  setIndustry: (industry: string) => void;

  /** Active input method */
  inputMethod: InputMethod;
  setInputMethod: (method: InputMethod) => void;

  /** Reset all fields to defaults */
  reset: () => void;
}

const DEFAULTS = {
  prompt: '',
  outputType: 'narrative' as OutputType,
  industry: DEFAULT_INDUSTRY,
  inputMethod: 'text' as InputMethod,
};

export const useNarrativeStore = create<NarrativeStore>((set) => ({
  ...DEFAULTS,
  setPrompt: (value) => set({ prompt: value }),
  setOutputType: (type) => set({ outputType: type }),
  setIndustry: (industry) => set({ industry }),
  setInputMethod: (method) => set({ inputMethod: method }),
  reset: () => set(DEFAULTS),
}));
