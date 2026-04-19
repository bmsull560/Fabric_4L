# Value Fabric Canonical Artifact Contracts
## TypeScript Interfaces Enforcing Typed Boundaries Between Agents

**Version:** 1.0.0  
**Status:** PRODUCTION DESIGN  
**Date:** April 2026

---

## 1. Shared Foundation

These interfaces are enforced across ALL agents and the frontend, eliminating schema drift and broken variable references.

### 1.1 Canonical Entity Reference (`EntityRef`)

Replaces ad-hoc IDs and labels.

```typescript
export interface EntityRef {  
  id: string;                    // UUID v4  
  canonicalName: string;         // Normalized name  
  entityType: EntityType;        // Canonical entity type  
  source: SourceType;  
  provenance: ProvenanceChain;  
  confidence: ConfidenceScore;  
}

export type EntityType =  
  | "Company" | "Product" | "Capability" | "UseCase" | "Persona"  
  | "Industry" | "ValueDriver" | "Metric" | "ProofPoint" | "Assumption"  
  | "Integration" | "TrustArtifact" | "CommercialModel" | "KnowledgeAsset";

export type SourceType =  
  | "WEBSITE_EXTRACTED" | "CRM_IMPORT" | "USER_INPUT"  
  | "INFERRED" | "BENCHMARK" | "ANALYST_REPORT";
```

### 1.2 Provenance and Confidence

```typescript
export interface ProvenanceChain {  
  originUrl?: string;  
  extractionTimestamp: ISO8601Timestamp;  
  extractorVersion: string;  
  llmModel?: string;  
  humanReviewed: boolean;  
  reviewDate?: ISO8601Timestamp;  
}

export interface ConfidenceScore {  
  score: number;                 // 0.0 - 1.0  
  baseWeight: number;            // Page-type authority  
  claimTypeMultiplier: number;   // EXPLICIT_METRIC = 1.0, etc.  
  corroborationBonus: number;    // 0.0, 0.10, 0.15  
  temporalPenalty: number;       // 0.0, -0.05, -0.10, -0.15  
  governanceFlags: GovernanceFlag[];  
}

export type GovernanceFlag =  
  | "NO_EVIDENCE_MAPPING"  
  | "NO_METRIC_OR_PROOFPOINT"  
  | "UNCORROBORATED_SINGLE_SOURCE"  
  | "EXCEEDS_BENCHMARK_RANGE"  
  | "ASSUMPTION_REQUIRES_VALIDATION"  
  | "TEMPORAL_DECAY_APPLIED"  
  | "DOUBLE_COUNT_RISK";

export type ISO8601Timestamp = string;
```

---

## 2. The Four Canonical Artifacts

### 2.1 Context Artifact

Owned by the `ContextExtractionAgent`. Consumed by the `ValueModelAgent`.

```typescript
export interface ContextArtifact {  
  version: "1.0.0";  
  artifactId: string;            // UUID  
  ownerAgent: "ContextExtractionAgent";  
  createdAt: ISO8601Timestamp;  
  updatedAt: ISO8601Timestamp;

  // --- Core Content ---  
  customerProfile: CustomerProfile;  
  businessContext: BusinessContext;  
  stakeholderMap: StakeholderMap;  
  painPointRegistry: PainPointRegistry;  
  initiativeRegistry: InitiativeRegistry;  
  processInventory: ProcessInventory;

  // --- Quality Metadata ---  
  completeness: CompletenessScore;  
  extractionSources: ExtractionSource[];  
  validationStatus: ValidationStatus;  
}
```

### 2.2 Value Model Artifact

Owned by the `ValueModelAgent`. Validated by the `IntegrityAgent`. Consumed by the `NarrativeAgent`.

```typescript
export interface ValueModelArtifact {  
  version: "1.0.0";  
  artifactId: string;            // UUID  
  ownerAgent: "ValueModelAgent";  
  contextRef: string;            // ContextArtifact.artifactId  
  createdAt: ISO8601Timestamp;  
  updatedAt: ISO8601Timestamp;

  // --- THE CRITICAL ADDITION: Variable Registry ---  
  // THIS RESOLVES: test_pack_variables_loadable  
  //                test_formula_variable_references_valid  
  //                test_manifest_variable_counts  
  variableRegistry: VariableRegistry;

  // --- Core Model Content ---  
  valueDrivers: ValueDriverEntry[];  
  useCaseModels: UseCaseModel[];  
  capabilityChains: CapabilityValueChain[];  
  kpiRegistry: KPIRegistry;  
  financialModel: FinancialModel;  
  assumptionRegistry: AssumptionRegistry;  // Shared with IntegrityAgent

  // --- Model Metadata ---  
  modelStatus: ModelStatus;  
  integrityRef?: string;         // IntegrityArtifact.artifactId (after review)  
  scenarioAnalyses: ScenarioAnalysis[];  
}
```

#### 2.2.1 Variable Registry

```typescript
export interface VariableRegistry {  
  variables: VariableDefinition[];  
  validationRules: VariableValidationRule[];  
  lastValidatedAt?: ISO8601Timestamp;  
  validationErrors: VariableValidationError[];  
}

export interface VariableDefinition {  
  id: string;                    // Unique variable ID  
  name: string;                  // Human-readable name  
  canonicalName: string;         // Normalized for formula references  
  source: VariableSource;  
  type: VariableType;  
  unit: MetricUnit;  
  defaultValue?: number;  
  currentValue?: number;         // Customer-specific if known  
  valueRange?: { min: number; max: number };  
  description: string;  
  // --- Traceability ---  
  provenance: ProvenanceChain;  
  confidence: ConfidenceScore;  
  // --- Links ---  
  usedInFormulas: string[];      // Formula IDs
}
```

### 2.3 Integrity Artifact

Owned by the `IntegrityAgent`. Validates the `ValueModelArtifact`.

```typescript
export interface IntegrityArtifact {  
  version: "1.0.0";  
  artifactId: string;  
  ownerAgent: "IntegrityAgent";  
  valueModelRef: string;         // ValueModelArtifact.artifactId  
  createdAt: ISO8601Timestamp;

  // --- Review Results ---  
  assumptionAudit: AssumptionAudit;  
  evidenceAssessment: EvidenceAssessment;  
  duplicationCheck: DuplicationCheck;  
  defensibilityReview: DefensibilityReview;  
  confidenceCalibration: ConfidenceCalibration;

  // --- Gate Status ---  
  gateResults: GateResult[];  
  overallStatus: IntegrityStatus;  
  promotionBlocked: boolean;  
  blockers: string[];  
}
```

### 2.4 Narrative Artifact

Owned by the `NarrativeAgent`. Consumes the `ValueModelArtifact` and `IntegrityArtifact`.

```typescript
export interface NarrativeArtifact {  
  version: "1.0.0";  
  artifactId: string;  
  ownerAgent: "NarrativeAgent";  
  valueModelRef: string;  
  integrityRef?: string;  
  createdAt: ISO8601Timestamp;

  // --- Outputs ---  
  executiveSummary: ExecutiveSummary;  
  valueNarrative: ValueNarrative;  
  stakeholderVersions: StakeholderVersion[];  
  objectionBrief: ObjectionResponse[];  
  expansionOpportunities: ExpansionOpportunity[];  
  realizationPlan: RealizationPlan;

  // --- Quality ---  
  bridgeVisibility: BridgeVisibilityScore;  
  traceabilityScore: number;     // 0-100  
  stakeholderCoverage: number;   // 0-100  
}
```

---

## 3. Schema Enforcement

The `SchemaValidator` ensures runtime enforcement of the canonical schema at every agent boundary and frontend interface.

```typescript
export interface SchemaValidator {  
  validateEntityRef(obj: unknown): obj is EntityRef;  
  validateContextArtifact(obj: unknown): obj is ContextArtifact;  
  validateValueModelArtifact(obj: unknown): obj is ValueModelArtifact;  
  validateIntegrityArtifact(obj: unknown): obj is IntegrityArtifact;  
  validateNarrativeArtifact(obj: unknown): obj is NarrativeArtifact;  
  validateVariableRegistry(obj: unknown): obj is VariableRegistry;  
}
```

### 3.1 Canonical Field Mapping

This is the ONE source of truth for migrating legacy fields to the canonical schema.

```typescript
export const CANONICAL_FIELD_MAP = {  
  // Old -> New (migrate once, then use new everywhere)  
  "label": "canonicalName",  
  "name": "canonicalName",       // When used as display name  
  "type": "entityType",  
  "entity_type": "entityType",  
  "node_type": "entityType",  
  "source_url": "provenance.originUrl",  
  "extracted_by": "provenance.extractorVersion",  
  "confidence_score": "confidence.score",  
} as const;
```
