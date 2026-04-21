/**
 * Workflow Type Definitions
 */

export interface ProspectInfo {
  companyId: string;
  companyName: string;
  contactName: string;
  contactTitle: string;
  industry?: string;
  revenue?: number;
  employees?: number;
}

export interface EnrichedEntity {
  id: string;
  name: string;
  type: string;
  confidence: number;
}

export interface WorkflowStep {
  path: string;
  label: string;
  description: string;
  icon: string;
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  { path: '/workflow', label: 'Prospect', description: 'Define target account', icon: 'Radar' },
  { path: '/workflow/intelligence', label: 'Intelligence', description: 'Research and enrich', icon: 'Building2' },
  { path: '/workflow/ai-model', label: 'AI Model', description: 'Generate hypotheses', icon: 'BrainCircuit' },
  { path: '/workflow/driver-tree', label: 'Driver Tree', description: 'Build structure', icon: 'GitFork' },
  { path: '/workflow/evidence', label: 'Evidence', description: 'Match evidence', icon: 'Database' },
  { path: '/workflow/calculator', label: 'Calculator', description: 'Model scenarios', icon: 'Calculator' },
  { path: '/workflow/value-case', label: 'Value Case', description: 'Generate case', icon: 'FileText' },
];
