"""Whitespace Analysis workflow implementation."""

import logging
from typing import Any

from ..models.agent_state import (
    GapAnalysis,
    WhitespaceAgentState,
    WhitespaceInputData,
    WorkflowStatus,
)
from ..models.workflow_config import WHITESPACE_WORKFLOW_CONFIG
from ..tools.registry import ToolRegistry
from .base import BaseWorkflow

logger = logging.getLogger(__name__)


class WhitespaceAnalysisWorkflow(BaseWorkflow):
    """Workflow for identifying gaps between prospect needs and solution capabilities.

    Pipeline:
    1. Analyze prospect needs from description and CRM data
    2. Query solution capabilities from knowledge graph
    3. Identify gaps through semantic matching
    4. Score opportunity potential
    5. Generate recommendations

    Example:
        workflow = WhitespaceAnalysisWorkflow(tool_registry)
        initial_state = workflow.create_initial_state({
            "prospect_id": "prospect-001",
            "prospect_needs": "We need to automate our invoice processing..."
        })
        result = await workflow.run(initial_state)
    """

    def __init__(self, tool_registry: ToolRegistry, checkpoint_saver=None):
        """Initialize Whitespace Analysis workflow."""
        super().__init__(
            config=WHITESPACE_WORKFLOW_CONFIG,
            tool_registry=tool_registry,
            checkpoint_saver=checkpoint_saver,
        )

    def _get_state_type(self):
        """Return Whitespace-specific state type."""
        return WhitespaceAgentState

    def create_initial_state(self, input_data: dict[str, Any]) -> WhitespaceAgentState:
        """Create initial state from input data."""
        whitespace_input = WhitespaceInputData(**input_data)

        return WhitespaceAgentState(
            workflow_type=self.config.workflow_type,
            status=WorkflowStatus.PENDING,
            whitespace_input=whitespace_input,
            input_data=input_data,
            output_data={},
            errors=[],
            metadata={"workflow_name": self.name},
        )

    async def _execute_tool(
        self, tool_name: str, state: WhitespaceAgentState, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool with Whitespace-specific input building."""

        if tool_name == "analyze_prospect_needs":
            return await self._execute_analyze_prospect(state)

        elif tool_name == "query_graph":
            return await self._execute_query_capabilities(state)

        elif tool_name == "identify_gaps":
            return await self._execute_identify_gaps(state)

        elif tool_name == "score_opportunity":
            return await self._execute_score_opportunity(state)

        return await super()._execute_tool(tool_name, state, config)

    async def _execute_analyze_prospect(self, state: WhitespaceAgentState) -> dict[str, Any]:
        """Analyze prospect needs using LLM extraction."""
        if not state.whitespace_input:
            return {"error": "No whitespace input configured"}

        needs_text = state.whitespace_input.prospect_needs

        # Get prospect data for context
        prospect_data = await self.tool_registry.execute(
            "get_prospect_data",
            {"prospect_id": state.whitespace_input.prospect_id, "data_types": ["profile"]},
        )

        profile = prospect_data.get("profile", {})

        # Use LLM to extract structured needs
        from openai import AsyncOpenAI

        api_key = self.config.get("openai_api_key") if self.config else None
        client = AsyncOpenAI(api_key=api_key)

        prompt = f"""Extract structured business needs from the following prospect description.
        
Prospect: {profile.get("name", "Unknown")}
Industry: {profile.get("industry", "Unknown")}
Description: {needs_text}

Extract needs as a JSON array of strings. Each need should be a clear, specific business requirement.
Example output: ["Reduce invoice processing time", "Improve data visibility across departments"]

Return ONLY the JSON array, no other text."""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3
            )
            import json

            content = response.choices[0].message.content.strip()
            # Extract JSON from potential markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            extracted_needs = json.loads(content)
        except Exception as e:
            logger.error(f"LLM need extraction failed: {e}")
            # Fallback to basic extraction
            extracted_needs = self._extract_needs_basic(needs_text)

        return {
            "extracted_needs": extracted_needs
            if isinstance(extracted_needs, list)
            else [extracted_needs],
            "need_count": len(extracted_needs) if isinstance(extracted_needs, list) else 1,
            "industry_context": profile.get("industry", "Unknown"),
            "company_size": profile.get("employees", 0),
            "analysis_confidence": 0.85,
        }

    def _extract_needs_basic(self, text: str) -> list[str]:
        """Basic keyword-based extraction as fallback."""
        sentences = text.replace(".", "|").replace("!", "|").replace("?", "|").split("|")

        need_keywords = ["need", "want", "require", "looking for", "challenge", "problem", "pain"]

        needs = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(kw in sentence.lower() for kw in need_keywords) and len(sentence) > 10:
                needs.append(sentence)

        if not needs and text.strip():
            needs = [text.strip()]

        return needs[:5]

    async def _execute_query_capabilities(self, state: WhitespaceAgentState) -> dict[str, Any]:
        """Query solution capabilities from knowledge graph."""
        # Query for capabilities
        query_result = await self.tool_registry.execute(
            "query_graph",
            {
                "cypher_query": """
                    MATCH (c:Capability)
                    WHERE c.status = 'VALIDATED'
                    RETURN c.id as id, c.name as name, 
                           c.description as description, c.category as category
                    LIMIT 100
                """,
                "parameters": {},
            },
        )

        capabilities = query_result.get("results", [])

        # Transform to simplified format
        simplified = [
            {
                "id": c.get("c.id", f"cap-{i}"),
                "name": c.get("c.name", "Unknown"),
                "description": c.get("c.description", ""),
                "category": c.get("c.category", "General"),
            }
            for i, c in enumerate(capabilities)
        ]

        return {
            "capabilities": simplified,
            "capability_count": len(simplified),
            "categories": list(set(c.get("category", "General") for c in simplified)),
        }

    async def _execute_identify_gaps(self, state: WhitespaceAgentState) -> dict[str, Any]:
        """Identify gaps between needs and capabilities using embeddings."""
        needs = state.output_data.get("analyze_prospect", {}).get("extracted_needs", [])
        capabilities = state.output_data.get("query_capabilities", {}).get("capabilities", [])

        if not needs:
            return {"error": "No needs extracted", "gaps": []}

        if not capabilities:
            return {"error": "No capabilities available", "gaps": []}

        gaps: list[GapAnalysis] = []

        # Use semantic search to find best matches
        for need in needs:
            best_match = None
            best_score = 0.0

            # Search for similar capabilities using semantic search
            try:
                search_result = await self.tool_registry.execute(
                    "semantic_search", {"query": need, "top_k": 3, "similarity_threshold": 0.5}
                )

                matches = search_result.get("results", [])
                if matches:
                    best_match = matches[0]
                    best_score = best_match.get("similarity_score", 0)
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
                # Fallback to simple text matching
                for cap in capabilities:
                    score = self._calculate_similarity(need, cap.get("description", ""))
                    if score > best_score:
                        best_score = score
                        best_match = cap

            # Determine gap type based on match score
            if best_score >= 0.7:
                gap_type = "none"
                impact = "low"
                recommendation = f"Strong match with capability: {best_match.get('name', 'N/A')}"
            elif best_score >= 0.4:
                gap_type = "coverage"
                impact = "medium"
                recommendation = (
                    f"Partial match - explore {best_match.get('name', 'N/A')} with customizations"
                )
            else:
                gap_type = "capability"
                impact = "high"
                recommendation = "New capability opportunity - engage solution engineering"

            gap = GapAnalysis(
                need_statement=need,
                matched_capability=best_match.get("name") if best_match else None,
                match_score=round(best_score, 2),
                gap_type=gap_type,
                impact=impact,
                recommendation=recommendation,
            )
            gaps.append(gap)

        return {
            "gaps": [g.model_dump() for g in gaps],
            "gap_count": len(gaps),
            "coverage_percentage": sum(1 for g in gaps if g.gap_type == "none") / len(gaps) * 100
            if gaps
            else 0,
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity as fallback."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2))

    async def _execute_score_opportunity(self, state: WhitespaceAgentState) -> dict[str, Any]:
        """Score overall opportunity potential."""
        gaps_data = state.output_data.get("identify_gaps", {})
        gaps = gaps_data.get("gaps", [])

        if not gaps:
            return {"score": 0, "assessment": "No gaps analyzed"}

        # Calculate opportunity score based on gap analysis
        high_impact_gaps = sum(1 for g in gaps if g.get("impact") == "high")
        medium_impact_gaps = sum(1 for g in gaps if g.get("impact") == "medium")

        # Score factors
        gap_factor = min(30, (high_impact_gaps * 10) + (medium_impact_gaps * 5))

        # Coverage factor (inverse - lower coverage means more whitespace)
        coverage = gaps_data.get("coverage_percentage", 0)
        whitespace_factor = max(0, (100 - coverage) / 2)

        # Need count factor (more needs = more opportunity)
        need_count = len(gaps)
        needs_factor = min(20, need_count * 4)

        total_score = gap_factor + whitespace_factor + needs_factor

        # Ensure score is 0-100
        total_score = min(100, max(0, total_score))

        # Generate assessment
        if total_score >= 70:
            assessment = "High opportunity - significant whitespace with clear needs"
        elif total_score >= 40:
            assessment = "Medium opportunity - some gaps to address"
        else:
            assessment = "Lower opportunity - good solution fit or unclear needs"

        # Generate recommendations
        recommendations = []

        if high_impact_gaps > 0:
            recommendations.append(f"Prioritize {high_impact_gaps} high-impact capability gaps")

        if coverage < 50:
            recommendations.append(
                "Significant whitespace exists - consider custom solution approach"
            )
        elif coverage > 80:
            recommendations.append("Strong fit - emphasize standard solution capabilities")

        if need_count >= 3:
            recommendations.append("Multiple needs identified - propose phased implementation")

        recommendations.append("Schedule technical deep-dive to validate assumptions")

        return {
            "opportunity_score": round(total_score, 1),
            "assessment": assessment,
            "factors": {
                "gap_contribution": round(gap_factor, 1),
                "whitespace_contribution": round(whitespace_factor, 1),
                "needs_contribution": round(needs_factor, 1),
            },
            "recommendations": recommendations,
        }
