# Major Decisions

> Record architectural or workflow choices that would be costly to re-debate.
> Use this template for each entry:

## YYYY-MM-DD: Decision title
**Decision:** _what was chosen_
**Rationale:** _why, in one or two sentences_
**Alternatives considered:** _what else was on the table and why rejected_
**Status:** active | revisited | superseded

## 2026-01-01: Four-layer memory separation
**Decision:** Split memory into working / episodic / semantic / personal rather than one flat folder.
**Rationale:** Each layer has different retention and retrieval needs. Flat memory breaks at ~6 weeks.
**Alternatives considered:** Flat directory (fails at scale), vector store (over-engineered for single user).
**Status:** active

## 2026-04-26: Add `design-md` seed skill (DESIGN.md / Google Stitch)
**Decision:** Ship a sixth seed skill, `design-md`, that points coding agents at a root `DESIGN.md` (Google Stitch format) as the visual-system source of truth. Loads only when `DESIGN.md` exists at the project root, default behavior is read-only on the contract file, and validation prefers `npx @google/design.md lint DESIGN.md` over hand-checks.
**Rationale:** `DESIGN.md` is becoming a de facto contract for AI-driven UI work; without an explicit skill, agents invent ad-hoc tokens that drift from the user's design system. Gating on `DESIGN.md`-existence keeps the skill silent on projects that don't use the format.
**Alternatives considered:** Bundle the rules into `git-proxy` or `skillforge` (wrong scope, wrong triggers); leave it to per-project `.agent/skills/` overrides (loses the cross-harness benefit); broader triggers like "UI"/"frontend"/"components"/"styling" (too generic, loads on every UI task even without DESIGN.md).
**Status:** active

## 2026-05-06: Six-layer microservices architecture
**Decision:** Value Fabric uses a six-layer microservices architecture with strict tenant isolation via PostgreSQL RLS.
**Rationale:** Separation of concerns across ingestion, extraction, knowledge graph, agents, ground truth, and benchmarks enables independent scaling and clear boundaries. RLS provides tenant isolation at the database level.
**Alternatives considered:** Monolithic architecture (harder to scale and maintain), shared-nothing microservices (too complex for current needs).
**Status:** active

## 2026-05-06: Canonical path structure
**Decision:** Runtime Python package root is `value_fabric/` with layer-specific subdirectories (layer1/ through layer6/). Service deployment layer is in `services/`. Frontend canonical location is `apps/web/`.
**Rationale:** Clear separation between runtime packages and service deployment layer. Legacy paths (frontend/, value-fabric/) retained for compatibility.
**Alternatives considered:** Flat structure (unclear boundaries), multiple package roots (complexity overhead).
**Status:** active

## 2026-05-06: Contracts as source of truth
**Decision:** All tool schemas and API shapes live in `contracts/` directory as the single source of truth.
**Rationale:** Enables drift detection, clear versioning, and automated validation across all layers.
**Alternatives considered:** Schema definitions in each service (drift risk), inline in code (hard to validate).
**Status:** active

## 2026-05-06: Provider-agnostic orchestration
**Decision:** Core orchestration logic in `value-fabric/layer4-agents/src/engine/` is provider-agnostic. Vendor-specific adapters (OpenAI, Anthropic, Neo4j, pgvector) are isolated.
**Rationale:** Enables easy swapping of LLM providers and databases without touching core logic.
**Alternatives considered:** Vendor-specific implementations throughout (lock-in risk), abstraction layer only (insufficient isolation).
**Status:** active
