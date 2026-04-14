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
  industry: 'Auto',
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
