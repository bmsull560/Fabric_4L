/**
 * Data Intelligence Layer (DIL) — Barrel Export
 *
 * Single import point for all DIL hooks, types, and error classes.
 *
 * Usage:
 *   import { useProducts, useAccountBriefing, type Product } from '@/hooks/dil';
 *
 * This module re-exports from 8 domain hook files covering 52 backend endpoints:
 *   L3: Products (12), Evidence (9), Competitive Intel (10), ROI Calculator (7)
 *   L4: Enrichment (4), Hypotheses (7), Narratives (5), Intelligence (3)
 */

// ── L3 Knowledge Graph Services ────────────────────────────────────────────

export {
  // Hooks
  useProducts,
  useProduct,
  useProductSignalMatching,
  usePortfolioSummary,
  useCapabilityCoverage,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
  useAddProductFeature,
  useDeleteProductFeature,
  useAddProductCapability,
  useDeleteProductCapability,
  // Types
  type Product,
  type ProductFeature,
  type CreateProductRequest,
  type UpdateProductRequest,
  type ProductListFilters,
  type ProductListResponse,
  type SignalMatch,
  type PortfolioSummary,
  type CapabilityCoverage,
  type AddFeatureRequest,
  type AddCapabilityRequest,
  // Error
  ProductApiError,
} from '../useProducts';

export {
  // Hooks
  useCaseStudies,
  useCaseStudy,
  useEvidenceIndustryStats,
  useEvidenceProductStats,
  useCreateCaseStudy,
  useUpdateCaseStudy,
  useDeleteCaseStudy,
  useBulkImportCaseStudies,
  useEvidenceSearch,
  // Types
  type CaseStudy,
  type CreateCaseStudyRequest,
  type UpdateCaseStudyRequest,
  type CaseStudyListFilters,
  type CaseStudyListResponse,
  type IndustryStats,
  type ProductStats,
  type EvidenceSearchRequest,
  type EvidenceSearchResult,
  type BulkImportRequest,
  type BulkImportResponse,
  // Error
  EvidenceApiError,
} from '../useEvidence';

export {
  // Hooks
  useCompetitors,
  useCompetitor,
  useBattlecards,
  useWinLossSummary,
  useLandscape,
  useCreateCompetitor,
  useUpdateCompetitor,
  useDeleteCompetitor,
  useCreateBattlecard,
  useRecordWinLoss,
  // Types
  type Competitor,
  type CreateCompetitorRequest,
  type UpdateCompetitorRequest,
  type CompetitorListFilters,
  type CompetitorListResponse,
  type Battlecard,
  type CreateBattlecardRequest,
  type WinLossOutcome,
  type WinLossRecord,
  type RecordWinLossRequest,
  type WinLossSummary,
  type LandscapeEntry,
  // Error
  CompetitiveIntelApiError,
} from '../useCompetitiveIntel';

export {
  // Hooks
  useROITemplates,
  useROICalculations,
  useROICalculation,
  useIndustryBenchmarks,
  useCalculateROI,
  useCompareROI,
  useCreateROITemplate,
  // Types
  type ROICalculationRequest,
  type ROICalculationResult,
  type AnnualProjection,
  type ScenarioResult,
  type ROICompareRequest,
  type ROICompareResult,
  type ROITemplate,
  type CreateROITemplateRequest,
  type ROICalculationListFilters,
  type ROICalculationListResponse,
  type IndustryBenchmark,
  // Error
  ROIApiError,
} from '../useROICalculator';

// ── L4 Agent Services ──────────────────────────────────────────────────────

export {
  // Hooks
  useEnrichmentStatus,
  useEnrichmentDetails,
  useEnrichAccount,
  useBatchEnrich,
  // Types
  type EnrichmentResult,
  type EnrichmentFinancials,
  type EnrichmentExecutive,
  type EnrichmentNewsItem,
  type EnrichAccountRequest,
  type BatchEnrichRequest,
  type BatchEnrichResponse,
  type EnrichmentCoverageStats,
  // Error
  EnrichmentApiError,
} from '../useEnrichment';

export {
  // Hooks
  useHypothesis,
  useAccountHypotheses,
  useHypothesisStats,
  useGenerateHypotheses,
  useValidateHypothesis,
  useDeleteHypothesis,
  useRankHypotheses,
  // Types
  type HypothesisStatus,
  type ValueHypothesis,
  type GenerateHypothesesRequest,
  type GenerateHypothesesResponse,
  type AccountHypothesesFilters,
  type AccountHypothesesResponse,
  type ValidateHypothesisRequest,
  type RankHypothesesRequest,
  type RankedHypothesis,
  type HypothesisStats,
  // Error
  HypothesisApiError,
} from '../useHypotheses';

export {
  // Hooks
  useNarratives,
  useNarrative,
  useGenerateNarrative,
  useUpdateNarrativeStatus,
  useDeleteNarrative,
  // Types
  type NarrativeTone,
  type NarrativeAudience,
  type NarrativeStatus,
  type NarrativeSection,
  type Narrative,
  type GenerateNarrativeRequest,
  type NarrativeListFilters,
  type NarrativeListResponse,
  type UpdateNarrativeStatusRequest,
  // Error
  NarrativeApiError,
} from '../useNarratives';

export {
  // Hooks
  useAccountBriefing,
  useDealReadiness,
  usePipelineSummary,
  // Types
  type AccountBriefing,
  type DealReadiness,
  type PipelineSummary,
  // Error
  IntelligenceApiError,
} from '../useIntelligence';
