/**
 * Value Pilot Type Definitions
 *
 * Cross-step state and API types for the 7-stage workflow.
 */

// Prospect Setup
export interface ProspectInfo {
  companyId: string;
  companyName: string;
  contactId?: string;
  contactName: string;
  contactTitle: string;
  employees?: number;
  revenue?: number;
  industry?: string;
  crmOpportunityId?: string;
}

// Intelligence
export interface EnrichedEntity {
  id: string;
  name: string;
  type: string;
  confidence: number;
  source: string;
  metadata?: Record<string, unknown>;
}

// AI Model
export interface ModelHypothesis {
  id: string;
  title: string;
  description: string;
  confidence: number;
  relatedEntities: string[];
  suggestedDrivers: string[];
}

// Driver Tree
export interface DriverTreeNode {
  id: string;
  name: string;
  type: 'root' | 'driver' | 'leaf';
  children?: DriverTreeNode[];
  formula?: string;
  value?: number;
  unit?: string;
}

export interface DriverTree {
  id: string;
  name: string;
  root: DriverTreeNode;
  entityId: string;
}

// Evidence
export interface EvidenceMatch {
  id: string;
  claim: string;
  evidenceType: 'metric' | 'document' | 'expert' | 'case_study';
  source: string;
  confidence: number;
  relevanceScore: number;
  extractionJobId?: string;
  verified: boolean;
}

// Calculator
export interface ScenarioConfig {
  baselineValue: number;
  variables: ScenarioVariable[];
  targetImprovement: number;
}

export interface ScenarioVariable {
  id: string;
  name: string;
  currentValue: number;
  projectedValue: number;
  unit: string;
  formula?: string;
}

export interface ScenarioResult {
  projectedValue: number;
  annualImpact: number;
  confidence: number;
  breakdown: Array<{ driver: string; contribution: number }>;
}

// Value Case
export interface ValueCase {
  id: string;
  title: string;
  prospectId: string;
  prospectName: string;
  summary: string;
  totalValue: number;
  confidence: number;
  timeHorizon: string;
  createdAt: string;
  status: 'draft' | 'review' | 'published' | 'archived';
  sections: ValueCaseSection[];
  exportFormats: ('pdf' | 'pptx' | 'docx')[];
}

export interface ValueCaseSection {
  id: string;
  type: 'executive_summary' | 'business_problem' | 'solution' | 'value_drivers' | 'financial_model' | 'evidence' | 'implementation' | 'next_steps';
  title: string;
  content: string;
  metrics?: Array<{ label: string; value: string; change?: string }>;
}

// Pilot State
export interface PilotSession {
  id: string;
  prospect: ProspectInfo | null;
  enrichedEntities: EnrichedEntity[];
  hypotheses: ModelHypothesis[];
  selectedTreeId: string | null;
  driverTree: DriverTree | null;
  evidenceMatches: EvidenceMatch[];
  scenario: ScenarioConfig | null;
  scenarioResult: ScenarioResult | null;
  generatedCaseId: string | null;
  valueCase: ValueCase | null;
  currentStep: number;
  createdAt: string;
  updatedAt: string;
}

// Navigation step config
export interface WorkflowStep {
  path: string;
  label: string;
  description: string;
  icon: string;
  requiredData?: string[];
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  { path: '/value-pilot', label: 'Prospect', description: 'Define target account and stakeholder', icon: 'Radar' },
  { path: '/value-pilot/intelligence', label: 'Intelligence', description: 'Research and enrich entity data', icon: 'Building2' },
  { path: '/value-pilot/ai-model', label: 'AI Model', description: 'Generate value hypotheses', icon: 'BrainCircuit' },
  { path: '/value-pilot/driver-tree', label: 'Driver Tree', description: 'Build value driver structure', icon: 'GitFork' },
  { path: '/value-pilot/evidence', label: 'Evidence', description: 'Match and verify evidence', icon: 'Database' },
  { path: '/value-pilot/calculator', label: 'Calculator', description: 'Model financial scenarios', icon: 'Calculator' },
  { path: '/value-pilot/value-case', label: 'Value Case', description: 'Generate business case', icon: 'FileText' },
];
