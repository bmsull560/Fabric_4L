"""
Narrative Builder Service — Data Intelligence Layer Phase 3, Task 3.1.

Generates structured sales narratives from Data Intelligence Layer data.
Assembles sections from across the value fabric:
  - Executive Summary (account context + top hypotheses)
  - Pain Points & Signals (from signal graph)
  - Value Hypotheses (ranked by chosen strategy)
  - Competitive Positioning (battlecards + win/loss)
  - ROI Projection (scenario comparison)
  - Evidence & Case Studies (industry-matched)

Architecture:
  - Template-based generation with customizable tone and audience
  - Pulls data from L3 (products, evidence, competitive intel, ROI)
    and L4 (enrichment, hypotheses) services
  - Stores generated narratives as Narrative nodes in Neo4j
  - Supports regeneration and versioning

Neo4j Node Schema:
  Narrative:
    id, tenant_id, account_id, title, audience, tone,
    sections (JSON), metadata (JSON),
    version, status, created_at, updated_at
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Enums & Data Models
# ---------------------------------------------------------------------------


class NarrativeTone(str, Enum):
    """Tone presets for narrative generation."""

    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    CONSULTATIVE = "consultative"


class NarrativeAudience(str, Enum):
    """Target audience presets."""

    C_SUITE = "c_suite"
    VP_DIRECTOR = "vp_director"
    TECHNICAL_BUYER = "technical_buyer"
    CHAMPION = "champion"
    EVALUATION_COMMITTEE = "evaluation_committee"


class NarrativeStatus(str, Enum):
    """Lifecycle status of a narrative."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DELIVERED = "delivered"


SECTION_ORDER = [
    "executive_summary",
    "pain_points",
    "value_hypotheses",
    "competitive_positioning",
    "roi_projection",
    "evidence",
    "next_steps",
]

# Tone-specific section templates
TONE_TEMPLATES: dict[str, dict[str, str]] = {
    "executive": {
        "executive_summary": "Based on our analysis of {company_name}, we have identified {hypothesis_count} value opportunities with a combined estimated impact of ${total_impact:,.0f} over {timeframe}.",
        "pain_points": "Our intelligence indicates {signal_count} active pain signals in your organization, with the highest-confidence signals in {top_signal_areas}.",
        "value_hypotheses": "We recommend focusing on the following {top_n} value drivers, ranked by {ranking_strategy}:",
        "competitive_positioning": "In the competitive landscape, our solution differentiates through {key_differentiators}. Our win rate against identified competitors is {win_rate:.0%}.",
        "roi_projection": "Under a {scenario} scenario over {months} months, we project a net benefit of ${net_benefit:,.0f} with a payback period of {payback:.1f} months and an ROI of {roi:.0f}%.",
        "evidence": "This is supported by {evidence_count} case studies in {industries}, demonstrating consistent results across similar organizations.",
        "next_steps": "We recommend the following next steps to advance this opportunity:",
    },
    "technical": {
        "executive_summary": "Technical assessment for {company_name}: {hypothesis_count} capability gaps identified with quantified impact of ${total_impact:,.0f}.",
        "pain_points": "{signal_count} technical pain signals detected. Primary areas: {top_signal_areas}.",
        "value_hypotheses": "Capability-to-signal mapping reveals {top_n} high-confidence matches (ranked by {ranking_strategy}):",
        "competitive_positioning": "Technical differentiation: {key_differentiators}. Head-to-head win rate: {win_rate:.0%}.",
        "roi_projection": "Financial model ({scenario}, {months}mo horizon): Net benefit ${net_benefit:,.0f}, payback {payback:.1f}mo, ROI {roi:.0f}%.",
        "evidence": "{evidence_count} technical case studies available across {industries}.",
        "next_steps": "Recommended technical validation steps:",
    },
    "financial": {
        "executive_summary": "Financial impact assessment for {company_name}: ${total_impact:,.0f} total addressable value across {hypothesis_count} opportunities.",
        "pain_points": "{signal_count} cost-impacting signals identified in current operations.",
        "value_hypotheses": "Top {top_n} value drivers by {ranking_strategy}:",
        "competitive_positioning": "Competitive TCO advantage: {key_differentiators}. Market win rate: {win_rate:.0%}.",
        "roi_projection": "{scenario} projection ({months}mo): Net ${net_benefit:,.0f}, {payback:.1f}mo payback, {roi:.0f}% ROI. NPV: ${npv:,.0f}.",
        "evidence": "Financial outcomes validated by {evidence_count} case studies in {industries}.",
        "next_steps": "Recommended financial validation steps:",
    },
    "consultative": {
        "executive_summary": "We've conducted a thorough analysis of {company_name}'s challenges and identified {hypothesis_count} areas where we can drive ${total_impact:,.0f} in measurable value.",
        "pain_points": "Through our discovery process, we've identified {signal_count} key challenges your team is facing, particularly in {top_signal_areas}.",
        "value_hypotheses": "Here are the {top_n} most impactful opportunities we've identified, prioritized by {ranking_strategy}:",
        "competitive_positioning": "What sets our approach apart: {key_differentiators}. Organizations choosing us over alternatives see a {win_rate:.0%} success rate.",
        "roi_projection": "In a {scenario} scenario over {months} months, you can expect ${net_benefit:,.0f} in net value with a {payback:.1f}-month payback and {roi:.0f}% return.",
        "evidence": "We've compiled {evidence_count} relevant success stories from {industries} that mirror your situation.",
        "next_steps": "Here's what we recommend as next steps:",
    },
}


@dataclass
class NarrativeRequest:
    """Request to generate a narrative."""

    tenant_id: str
    account_id: str
    title: str = "Account Intelligence Narrative"
    tone: str = "executive"
    audience: str = "c_suite"
    include_sections: list[str] = field(default_factory=lambda: list(SECTION_ORDER))
    ranking_strategy: str = "balanced"
    roi_scenario: str = "moderate"
    roi_time_horizon_months: int = 36
    top_n_hypotheses: int = 5
    custom_next_steps: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Narrative Builder Service
# ---------------------------------------------------------------------------


class NarrativeBuilderService:
    """Service for generating structured sales narratives."""

    def __init__(self, neo4j_driver: Any):
        self._driver = neo4j_driver

    # ------------------------------------------------------------------
    # Core Generation
    # ------------------------------------------------------------------

    async def generate_narrative(
        self,
        request: NarrativeRequest,
        *,
        account_data: dict[str, Any] | None = None,
        signals_data: list[dict[str, Any]] | None = None,
        hypotheses_data: list[dict[str, Any]] | None = None,
        competitive_data: dict[str, Any] | None = None,
        roi_data: dict[str, Any] | None = None,
        evidence_data: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate a complete narrative from assembled intelligence data.

        This method accepts pre-fetched data from the orchestration layer
        so it can be used both standalone and as part of a larger pipeline.
        """
        narrative_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        # Build context for template rendering
        context = self._build_context(
            request=request,
            account_data=account_data or {},
            signals_data=signals_data or [],
            hypotheses_data=hypotheses_data or [],
            competitive_data=competitive_data or {},
            roi_data=roi_data or {},
            evidence_data=evidence_data or [],
        )

        # Generate each requested section
        sections = {}
        for section_key in request.include_sections:
            if section_key in SECTION_ORDER:
                sections[section_key] = self._render_section(
                    section_key, request.tone, context
                )

        # Assemble the narrative
        narrative = {
            "id": narrative_id,
            "tenant_id": request.tenant_id,
            "account_id": request.account_id,
            "title": request.title,
            "audience": request.audience,
            "tone": request.tone,
            "sections": sections,
            "metadata": {
                "hypothesis_count": context.get("hypothesis_count", 0),
                "signal_count": context.get("signal_count", 0),
                "evidence_count": context.get("evidence_count", 0),
                "total_impact": context.get("total_impact", 0),
                "ranking_strategy": request.ranking_strategy,
                "roi_scenario": request.roi_scenario,
                "generated_at": now,
            },
            "version": 1,
            "status": NarrativeStatus.DRAFT.value,
            "created_at": now,
            "updated_at": now,
        }

        # Persist to Neo4j
        stored = await self._store_narrative(narrative)

        logger.info(
            "narrative_generated",
            narrative_id=narrative_id,
            account_id=request.account_id,
            sections=list(sections.keys()),
        )

        return stored

    # ------------------------------------------------------------------
    # Section Rendering
    # ------------------------------------------------------------------

    def _build_context(
        self,
        request: NarrativeRequest,
        account_data: dict[str, Any],
        signals_data: list[dict[str, Any]],
        hypotheses_data: list[dict[str, Any]],
        competitive_data: dict[str, Any],
        roi_data: dict[str, Any],
        evidence_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build a unified context dict for template rendering."""
        # Extract key metrics
        total_impact = sum(
            h.get("estimated_impact_usd", 0) for h in hypotheses_data
        )
        top_signal_areas = ", ".join(
            sorted(
                {s.get("category", "general") for s in signals_data[:5]}
            )
        ) or "multiple areas"

        # Competitive metrics
        win_rate = competitive_data.get("overall_win_rate", 0)
        landscape = competitive_data.get("landscape", [])
        key_differentiators = ", ".join(
            competitive_data.get("key_differentiators", ["integrated platform", "data-driven insights"])
        )

        # ROI metrics
        roi_results = roi_data.get("results", {})
        scenarios = roi_data.get("scenarios", {})
        moderate = scenarios.get(request.roi_scenario, roi_results)

        # Evidence metrics
        industries = ", ".join(
            sorted({e.get("industry", "general") for e in evidence_data[:10]})
        ) or "various industries"

        return {
            "company_name": account_data.get("name", account_data.get("company_name", "the account")),
            "hypothesis_count": len(hypotheses_data),
            "signal_count": len(signals_data),
            "evidence_count": len(evidence_data),
            "total_impact": total_impact,
            "top_signal_areas": top_signal_areas,
            "top_n": min(request.top_n_hypotheses, len(hypotheses_data)),
            "ranking_strategy": request.ranking_strategy,
            "key_differentiators": key_differentiators,
            "win_rate": win_rate,
            "scenario": request.roi_scenario,
            "months": request.roi_time_horizon_months,
            "timeframe": f"{request.roi_time_horizon_months} months",
            "net_benefit": moderate.get("net_benefit_3year", moderate.get("net_benefit_year1", 0)),
            "payback": moderate.get("payback_months", 0),
            "roi": moderate.get("roi_pct_3year", moderate.get("roi_pct_year1", 0)),
            "npv": moderate.get("npv", 0),
            # Raw data for detailed sections
            "hypotheses": hypotheses_data[:request.top_n_hypotheses],
            "signals": signals_data,
            "competitors": landscape,
            "evidence": evidence_data,
            "roi_scenarios": scenarios,
            "custom_next_steps": request.custom_next_steps,
        }

    def _render_section(
        self, section_key: str, tone: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Render a single narrative section."""
        templates = TONE_TEMPLATES.get(tone, TONE_TEMPLATES["executive"])
        template = templates.get(section_key, "")

        # Safe format with fallbacks
        try:
            summary_text = template.format(**context)
        except (KeyError, ValueError, IndexError):
            summary_text = template

        section: dict[str, Any] = {
            "title": section_key.replace("_", " ").title(),
            "summary": summary_text,
        }

        # Add structured detail data per section type
        if section_key == "value_hypotheses":
            section["items"] = [
                {
                    "hypothesis": h.get("hypothesis_text", ""),
                    "product": h.get("product_name", ""),
                    "signal": h.get("signal_name", ""),
                    "confidence": h.get("confidence_score", 0),
                    "impact_usd": h.get("estimated_impact_usd", 0),
                }
                for h in context.get("hypotheses", [])
            ]

        elif section_key == "pain_points":
            section["items"] = [
                {
                    "name": s.get("name", ""),
                    "category": s.get("category", ""),
                    "confidence": s.get("confidence_score", 0),
                    "impact_value": s.get("impact_value", 0),
                }
                for s in context.get("signals", [])[:10]
            ]

        elif section_key == "competitive_positioning":
            section["competitors"] = [
                {
                    "name": c.get("competitor", {}).get("name", c.get("name", "")),
                    "market_position": c.get("competitor", {}).get("market_position", c.get("market_position", "")),
                    "win_rate": c.get("win_rate", 0),
                    "threat_level": c.get("threat_level", ""),
                }
                for c in context.get("competitors", [])[:5]
            ]

        elif section_key == "roi_projection":
            section["scenarios"] = context.get("roi_scenarios", {})

        elif section_key == "evidence":
            section["case_studies"] = [
                {
                    "title": e.get("title", ""),
                    "industry": e.get("industry", ""),
                    "company_size": e.get("company_size", ""),
                    "outcome_summary": e.get("outcome_summary", ""),
                }
                for e in context.get("evidence", [])[:5]
            ]

        elif section_key == "next_steps":
            custom = context.get("custom_next_steps", [])
            if custom:
                section["items"] = custom
            else:
                section["items"] = [
                    "Schedule a technical deep-dive with your team",
                    "Review and validate the ROI assumptions together",
                    "Identify a pilot use case for initial deployment",
                    "Align on success metrics and timeline",
                ]

        return section

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    async def _store_narrative(self, narrative: dict[str, Any]) -> dict[str, Any]:
        """Store a narrative in Neo4j."""
        query = """
        CREATE (n:Narrative {
            id: $id,
            tenant_id: $tenant_id,
            account_id: $account_id,
            title: $title,
            audience: $audience,
            tone: $tone,
            sections: $sections,
            metadata: $metadata,
            version: $version,
            status: $status,
            entity_type: 'Narrative',
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN n {.*} AS narrative
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "id": narrative["id"],
                "tenant_id": narrative["tenant_id"],
                "account_id": narrative["account_id"],
                "title": narrative["title"],
                "audience": narrative["audience"],
                "tone": narrative["tone"],
                "sections": json.dumps(narrative["sections"]),
                "metadata": json.dumps(narrative["metadata"]),
                "version": narrative["version"],
                "status": narrative["status"],
                "created_at": narrative["created_at"],
                "updated_at": narrative["updated_at"],
            })
            record = await result.single()

        stored = narrative.copy()
        if record and record["narrative"]:
            stored["id"] = record["narrative"].get("id", narrative["id"])
        return stored

    async def get_narrative(
        self, tenant_id: str, narrative_id: str
    ) -> dict[str, Any] | None:
        """Retrieve a stored narrative."""
        query = """
        MATCH (n:Narrative {id: $narrative_id, tenant_id: $tenant_id})
        RETURN n {.*} AS narrative
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "narrative_id": narrative_id,
                "tenant_id": tenant_id,
            })
            record = await result.single()

        if not record or not record["narrative"]:
            return None

        narr = record["narrative"]
        for json_field in ("sections", "metadata"):
            if isinstance(narr.get(json_field), str):
                try:
                    narr[json_field] = json.loads(narr[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return narr

    async def list_narratives(
        self,
        tenant_id: str,
        *,
        account_id: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List narratives with optional filtering."""
        where_clauses = ["n.tenant_id = $tenant_id"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "skip": skip,
            "limit": limit,
        }

        if account_id:
            where_clauses.append("n.account_id = $account_id")
            params["account_id"] = account_id

        if status:
            where_clauses.append("n.status = $status")
            params["status"] = status

        where = " AND ".join(where_clauses)

        count_query = f"MATCH (n:Narrative) WHERE {where} RETURN count(n) AS total"
        list_query = f"""
        MATCH (n:Narrative) WHERE {where}
        RETURN n {{.id, .title, .audience, .tone, .status, .version, .account_id, .created_at, .updated_at}} AS narrative
        ORDER BY n.updated_at DESC
        SKIP $skip LIMIT $limit
        """

        async with self._driver.session() as session:
            count_result = await session.run(count_query, params)
            count_record = await count_result.single()
            total = count_record["total"] if count_record else 0

            list_result = await session.run(list_query, params)
            records = [record async for record in list_result]

        return {
            "narratives": [r["narrative"] for r in records],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update_status(
        self, tenant_id: str, narrative_id: str, new_status: str
    ) -> dict[str, Any] | None:
        """Update narrative status."""
        now = datetime.now(UTC).isoformat()
        query = """
        MATCH (n:Narrative {id: $narrative_id, tenant_id: $tenant_id})
        SET n.status = $status, n.updated_at = $now
        RETURN n {.*} AS narrative
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "narrative_id": narrative_id,
                "tenant_id": tenant_id,
                "status": new_status,
                "now": now,
            })
            record = await result.single()

        if not record or not record["narrative"]:
            return None

        narr = record["narrative"]
        for json_field in ("sections", "metadata"):
            if isinstance(narr.get(json_field), str):
                try:
                    narr[json_field] = json.loads(narr[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return narr

    async def delete_narrative(
        self, tenant_id: str, narrative_id: str
    ) -> bool:
        """Delete a narrative."""
        query = """
        MATCH (n:Narrative {id: $narrative_id, tenant_id: $tenant_id})
        DELETE n
        RETURN count(n) AS deleted
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "narrative_id": narrative_id,
                "tenant_id": tenant_id,
            })
            record = await result.single()

        return bool(record and record["deleted"] > 0)
