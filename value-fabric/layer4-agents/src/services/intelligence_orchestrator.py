"""
Intelligence Orchestrator — Data Intelligence Layer Phase 3, Task 3.2.

Provides cross-layer orchestration that assembles intelligence from
all DIL services into unified deliverables:

  - Account Intelligence Briefing: Full account dossier combining
    enrichment, signals, hypotheses, competitive intel, ROI, evidence
  - Deal Readiness Score: Composite score indicating how prepared
    the sales team is to engage an account
  - Pipeline Intelligence Summary: Aggregated intelligence across
    all active accounts

Architecture:
  - Orchestrates calls across L3 (Neo4j) and L4 (PostgreSQL + Neo4j)
  - Each method accepts service instances or creates them from drivers
  - Designed for use by the route layer which injects dependencies
  - All methods are tenant-scoped
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Deal Readiness Scoring Weights
# ---------------------------------------------------------------------------

READINESS_WEIGHTS = {
    "enrichment_complete": 0.15,
    "signals_identified": 0.15,
    "hypotheses_generated": 0.20,
    "hypotheses_validated": 0.10,
    "competitive_intel": 0.10,
    "roi_calculated": 0.15,
    "evidence_matched": 0.10,
    "narrative_generated": 0.05,
}

READINESS_THRESHOLDS = {
    "not_ready": 0.0,
    "early_stage": 0.20,
    "developing": 0.40,
    "prepared": 0.60,
    "deal_ready": 0.80,
}


def _readiness_label(score: float) -> str:
    """Map a readiness score to a human-readable label."""
    if score >= READINESS_THRESHOLDS["deal_ready"]:
        return "deal_ready"
    if score >= READINESS_THRESHOLDS["prepared"]:
        return "prepared"
    if score >= READINESS_THRESHOLDS["developing"]:
        return "developing"
    if score >= READINESS_THRESHOLDS["early_stage"]:
        return "early_stage"
    return "not_ready"


# ---------------------------------------------------------------------------
# Intelligence Orchestrator
# ---------------------------------------------------------------------------


class IntelligenceOrchestrator:
    """Cross-layer orchestrator for unified intelligence deliverables."""

    def __init__(self, neo4j_driver: Any, db: Any | None = None):
        self._driver = neo4j_driver
        self._db = db

    # ------------------------------------------------------------------
    # Account Intelligence Briefing
    # ------------------------------------------------------------------

    async def get_account_briefing(
        self,
        tenant_id: str,
        account_id: str,
        *,
        include_narrative: bool = False,
        top_n_hypotheses: int = 5,
        roi_scenario: str = "moderate",
    ) -> dict[str, Any]:
        """Assemble a complete intelligence briefing for an account.

        Gathers data from all DIL services in parallel-safe sequence:
          1. Account enrichment status
          2. Active signals for the account
          3. Value hypotheses (ranked)
          4. Competitive landscape
          5. ROI projection
          6. Matched evidence / case studies
          7. Optionally: generated narrative
        """
        now = datetime.now(UTC).isoformat()

        # Gather all intelligence components
        signals = await self._get_account_signals(tenant_id, account_id)
        hypotheses = await self._get_account_hypotheses(tenant_id, account_id, top_n_hypotheses)
        competitive = await self._get_competitive_landscape(tenant_id)
        roi = await self._get_roi_summary(tenant_id, account_id)
        evidence = await self._get_matched_evidence(tenant_id, account_id)
        narrative_summary = None

        if include_narrative:
            narrative_summary = await self._get_latest_narrative(tenant_id, account_id)

        # Compute deal readiness
        readiness = self._compute_deal_readiness(
            signals=signals,
            hypotheses=hypotheses,
            competitive=competitive,
            roi=roi,
            evidence=evidence,
            narrative=narrative_summary,
        )

        briefing = {
            "briefing_id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "account_id": account_id,
            "generated_at": now,
            "deal_readiness": readiness,
            "sections": {
                "signals": {
                    "count": len(signals),
                    "top_signals": signals[:5],
                },
                "value_hypotheses": {
                    "count": len(hypotheses),
                    "top_hypotheses": hypotheses,
                },
                "competitive_landscape": competitive,
                "roi_projection": roi,
                "evidence": {
                    "count": len(evidence),
                    "case_studies": evidence[:5],
                },
            },
        }

        if narrative_summary:
            briefing["sections"]["narrative"] = narrative_summary

        logger.info(
            "account_briefing_generated",
            account_id=account_id,
            readiness_score=readiness["score"],
            readiness_label=readiness["label"],
        )

        return briefing

    # ------------------------------------------------------------------
    # Deal Readiness Score
    # ------------------------------------------------------------------

    async def get_deal_readiness(
        self, tenant_id: str, account_id: str
    ) -> dict[str, Any]:
        """Calculate deal readiness score for an account."""
        signals = await self._get_account_signals(tenant_id, account_id)
        hypotheses = await self._get_account_hypotheses(tenant_id, account_id, limit=20)
        competitive = await self._get_competitive_landscape(tenant_id)
        roi = await self._get_roi_summary(tenant_id, account_id)
        evidence = await self._get_matched_evidence(tenant_id, account_id)
        narrative = await self._get_latest_narrative(tenant_id, account_id)

        readiness = self._compute_deal_readiness(
            signals=signals,
            hypotheses=hypotheses,
            competitive=competitive,
            roi=roi,
            evidence=evidence,
            narrative=narrative,
        )

        return {
            "account_id": account_id,
            "generated_at": datetime.now(UTC).isoformat(),
            **readiness,
        }

    def _compute_deal_readiness(
        self,
        *,
        signals: list[dict],
        hypotheses: list[dict],
        competitive: dict,
        roi: dict,
        evidence: list[dict],
        narrative: dict | None,
    ) -> dict[str, Any]:
        """Compute a weighted deal readiness score."""
        components: dict[str, float] = {}

        # Signals identified (0-1 based on count, cap at 5)
        components["signals_identified"] = min(len(signals) / 5, 1.0)

        # Hypotheses generated (0-1 based on count, cap at 5)
        components["hypotheses_generated"] = min(len(hypotheses) / 5, 1.0)

        # Hypotheses validated (ratio of validated to total)
        validated = sum(1 for h in hypotheses if h.get("status") == "validated")
        components["hypotheses_validated"] = (
            validated / len(hypotheses) if hypotheses else 0.0
        )

        # Competitive intel available
        comp_count = competitive.get("total_competitors", 0)
        components["competitive_intel"] = min(comp_count / 3, 1.0)

        # ROI calculated
        has_roi = bool(roi.get("calculations") or roi.get("results"))
        components["roi_calculated"] = 1.0 if has_roi else 0.0

        # Evidence matched
        components["evidence_matched"] = min(len(evidence) / 3, 1.0)

        # Narrative generated
        components["narrative_generated"] = 1.0 if narrative else 0.0

        # Enrichment (assume complete if we have signals — simplified)
        components["enrichment_complete"] = 1.0 if signals else 0.0

        # Weighted score
        score = sum(
            components.get(k, 0) * w
            for k, w in READINESS_WEIGHTS.items()
        )
        score = round(min(score, 1.0), 3)

        return {
            "score": score,
            "label": _readiness_label(score),
            "components": {k: round(v, 3) for k, v in components.items()},
            "recommendations": self._generate_recommendations(components),
        }

    @staticmethod
    def _generate_recommendations(components: dict[str, float]) -> list[str]:
        """Generate actionable recommendations based on gaps."""
        recs = []
        if components.get("signals_identified", 0) < 0.5:
            recs.append("Run signal detection to identify more pain points for this account")
        if components.get("hypotheses_generated", 0) < 0.5:
            recs.append("Generate value hypotheses to map signals to product capabilities")
        if components.get("hypotheses_validated", 0) < 0.3:
            recs.append("Validate existing hypotheses with the prospect to increase confidence")
        if components.get("competitive_intel", 0) < 0.5:
            recs.append("Add competitive intelligence — identify key competitors in this deal")
        if components.get("roi_calculated", 0) < 1.0:
            recs.append("Run an ROI calculation to quantify the value proposition")
        if components.get("evidence_matched", 0) < 0.5:
            recs.append("Find relevant case studies and evidence to support the value story")
        if components.get("narrative_generated", 0) < 1.0:
            recs.append("Generate a sales narrative to package the intelligence for delivery")
        return recs

    # ------------------------------------------------------------------
    # Pipeline Intelligence
    # ------------------------------------------------------------------

    async def get_pipeline_summary(
        self, tenant_id: str
    ) -> dict[str, Any]:
        """Get aggregated intelligence across all accounts."""
        query = """
        MATCH (vh:ValueHypothesis {tenant_id: $tenant_id})
        WITH vh.account_id AS account_id,
             count(vh) AS hypothesis_count,
             avg(vh.confidence_score) AS avg_confidence,
             sum(vh.estimated_impact_usd) AS total_impact,
             collect(DISTINCT vh.status) AS statuses
        RETURN account_id,
               hypothesis_count,
               avg_confidence,
               total_impact,
               statuses
        ORDER BY total_impact DESC
        """
        async with self._driver.session() as session:
            result = await session.run(query, {"tenant_id": tenant_id})
            records = [record async for record in result]

        accounts = []
        total_pipeline_value = 0.0
        total_hypotheses = 0

        for r in records:
            acct_impact = r["total_impact"] or 0
            acct_hypotheses = r["hypothesis_count"] or 0
            statuses = r["statuses"] or []

            total_pipeline_value += acct_impact
            total_hypotheses += acct_hypotheses

            accounts.append({
                "account_id": r["account_id"],
                "hypothesis_count": acct_hypotheses,
                "avg_confidence": round(r["avg_confidence"] or 0, 3),
                "total_impact": round(acct_impact, 2),
                "has_validated": "validated" in statuses,
                "has_converted": "converted" in statuses,
            })

        return {
            "tenant_id": tenant_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_accounts": len(accounts),
                "total_hypotheses": total_hypotheses,
                "total_pipeline_value": round(total_pipeline_value, 2),
                "avg_hypotheses_per_account": (
                    round(total_hypotheses / len(accounts), 1) if accounts else 0
                ),
            },
            "accounts": accounts,
        }

    # ------------------------------------------------------------------
    # Internal Data Fetchers (Neo4j)
    # ------------------------------------------------------------------

    async def _get_account_signals(
        self, tenant_id: str, account_id: str
    ) -> list[dict[str, Any]]:
        """Fetch signals associated with an account."""
        query = """
        MATCH (s:Signal {tenant_id: $tenant_id})
        WHERE s.account_id = $account_id OR s.target_account_id = $account_id
        RETURN s {.*} AS signal
        ORDER BY s.confidence_score DESC
        LIMIT 20
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "tenant_id": tenant_id,
                "account_id": account_id,
            })
            records = [record async for record in result]
        return [r["signal"] for r in records]

    async def _get_account_hypotheses(
        self, tenant_id: str, account_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Fetch value hypotheses for an account."""
        query = """
        MATCH (vh:ValueHypothesis {tenant_id: $tenant_id, account_id: $account_id})
        RETURN vh {.*} AS hypothesis
        ORDER BY vh.confidence_score DESC
        LIMIT $limit
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "tenant_id": tenant_id,
                "account_id": account_id,
                "limit": limit,
            })
            records = [record async for record in result]
        return [r["hypothesis"] for r in records]

    async def _get_competitive_landscape(
        self, tenant_id: str
    ) -> dict[str, Any]:
        """Fetch competitive landscape summary."""
        query = """
        MATCH (c:Competitor {tenant_id: $tenant_id})
        OPTIONAL MATCH (c)<-[won:WON_AGAINST]-(p1:Product)
        OPTIONAL MATCH (c)<-[lost:LOST_TO]-(p2:Product)
        RETURN count(DISTINCT c) AS total_competitors,
               count(DISTINCT won) AS total_wins,
               count(DISTINCT lost) AS total_losses
        """
        async with self._driver.session() as session:
            result = await session.run(query, {"tenant_id": tenant_id})
            record = await result.single()

        if not record:
            return {"total_competitors": 0, "total_wins": 0, "total_losses": 0}

        total_wins = record["total_wins"] or 0
        total_losses = record["total_losses"] or 0
        total_deals = total_wins + total_losses

        return {
            "total_competitors": record["total_competitors"] or 0,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "overall_win_rate": round(total_wins / total_deals, 3) if total_deals > 0 else 0,
        }

    async def _get_roi_summary(
        self, tenant_id: str, account_id: str
    ) -> dict[str, Any]:
        """Fetch most recent ROI calculation for an account."""
        query = """
        MATCH (rc:ROICalculation {tenant_id: $tenant_id, account_id: $account_id})
        RETURN rc {.*} AS calculation
        ORDER BY rc.created_at DESC
        LIMIT 1
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "tenant_id": tenant_id,
                "account_id": account_id,
            })
            record = await result.single()

        if not record or not record["calculation"]:
            return {}

        import json
        calc = record["calculation"]
        for json_field in ("inputs", "outputs", "assumptions"):
            if isinstance(calc.get(json_field), str):
                try:
                    calc[json_field] = json.loads(calc[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return calc

    async def _get_matched_evidence(
        self, tenant_id: str, account_id: str
    ) -> list[dict[str, Any]]:
        """Fetch evidence/case studies relevant to an account's industry."""
        query = """
        MATCH (e:Evidence {tenant_id: $tenant_id})
        RETURN e {.*} AS evidence
        ORDER BY e.created_at DESC
        LIMIT 10
        """
        async with self._driver.session() as session:
            result = await session.run(query, {"tenant_id": tenant_id})
            records = [record async for record in result]
        return [r["evidence"] for r in records]

    async def _get_latest_narrative(
        self, tenant_id: str, account_id: str
    ) -> dict[str, Any] | None:
        """Fetch the most recent narrative for an account."""
        query = """
        MATCH (n:Narrative {tenant_id: $tenant_id, account_id: $account_id})
        RETURN n {.id, .title, .status, .tone, .audience, .version, .created_at} AS narrative
        ORDER BY n.updated_at DESC
        LIMIT 1
        """
        async with self._driver.session() as session:
            result = await session.run(query, {
                "tenant_id": tenant_id,
                "account_id": account_id,
            })
            record = await result.single()

        if not record or not record["narrative"]:
            return None
        return record["narrative"]
