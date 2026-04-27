# Deprecated: Old 6-Stage Value Studio

These files are the original 6-stage Value Studio pipeline that has been superseded
by the new workspace-based Value Studio (`/studio/:accountId/*`).

All `/model/value-studio/*` routes now redirect to the new workspace system.
These files contain **100% hardcoded mock data** with zero API connections.

**Replaced by:**
- `pages/studio/ActionPlanTab.tsx` (replaces Stage2Mapping)
- `pages/studio/ValueModelTab.tsx` (replaces Stage3Modeling + Stage4Validation)
- `pages/studio/NarrativeTab.tsx` (replaces Stage5Narrative)
- `pages/studio/StudioEnrichmentTab.tsx` (new — DIL enrichment)
- `pages/studio/StudioCompetitiveTab.tsx` (new — DIL competitive intel)
- `pages/studio/StudioROITab.tsx` (new — DIL ROI calculator)
- `pages/studio/StudioEvidenceTab.tsx` (new — DIL evidence library)

**Safe to delete** after confirming no external links reference the old stage URLs.

Deprecated: Sprint 3 — Data Intelligence Layer integration
