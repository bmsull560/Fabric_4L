"""Value Tree Projection Agent.

Implements value tree traversal and projection algorithms for:
- Upward traversal (outcome discovery)
- Downward traversal (capability discovery)
- Semantic matching for node alignment
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neo4j import AsyncDriver

from .base import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class ValueTreeNode:
    """Node in the Value Tree."""

    node_id: str
    node_type: str  # 'outcome', 'value_driver', 'use_case', 'capability', 'feature'
    name: str
    description: str
    parent_ids: list[str]
    child_ids: list[str]
    metrics: list[dict[str, Any]]
    formulas: list[dict[str, Any]]
    semantic_embedding: list[float] | None = None
    metadata: dict[str, Any] = None


@dataclass
class ProjectionResult:
    """Result of projecting pain points onto Value Tree."""

    projection_id: str
    pain_point_id: str
    matched_nodes: list[dict[str, Any]]
    match_scores: dict[str, float]
    traversal_path: list[str]
    confidence: float
    projection_timestamp: str


class ValueTreeProjectionAgent(BaseAgent):
    """Agent for value tree projection and traversal.

    Capabilities:
    - semantic_matching: Match entities to value tree nodes
    - graph_traversal: Navigate up/down the value tree
    - node_classification: Categorize nodes by type
    - relationship_inference: Infer relationships between nodes
    """

    def __init__(self, driver: AsyncDriver | None = None):
        """Initialize value tree projection agent.

        Args:
            driver: Neo4j async driver for graph operations
        """
        super().__init__("ValueTreeProjectionAgent")
        self._driver = driver

    async def execute(self, context: dict[str, Any]) -> AgentResult:
        """Execute value tree projection.

        Args:
            context: Must contain:
                - operation: 'upward_traversal', 'downward_traversal', or 'semantic_match'
                - start_node_id: Starting node ID
                - Optional: max_hops (default 5)
                - Optional: min_confidence (default 0.7)
                - Optional: tenant_id (default 'system')

        Returns:
            AgentResult with projection results
        """
        start_time = time.time()

        try:
            operation = context.get("operation", "upward_traversal")
            start_node_id = context.get("start_node_id")
            max_hops = context.get("max_hops", 5)
            min_confidence = context.get("min_confidence", 0.7)
            tenant_id = context.get("tenant_id", "system")

            if not start_node_id:
                return self._create_result(
                    status="failed",
                    output={},
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    errors=["start_node_id is required"],
                )

            if operation == "upward_traversal":
                result = await self._upward_traversal(start_node_id, max_hops, tenant_id)
            elif operation == "downward_traversal":
                result = await self._downward_traversal(start_node_id, max_hops, tenant_id)
            elif operation == "semantic_match":
                query_text = context.get("query_text", "")
                result = await self._semantic_match(query_text, min_confidence, tenant_id)
            else:
                return self._create_result(
                    status="failed",
                    output={},
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    errors=[f"Unknown operation: {operation}"],
                )

            return self._create_result(
                status="success",
                output=result,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            logger.error(f"Value tree projection failed: {e}")
            return self._create_result(
                status="failed",
                output={},
                execution_time_ms=int((time.time() - start_time) * 1000),
                errors=[str(e)],
            )

    async def _upward_traversal(
        self, start_node_id: str, max_hops: int = 5, tenant_id: str = "system"
    ) -> dict[str, Any]:
        """Traverse upward from capability to outcomes.

        Cypher pattern:
        MATCH path = (start)-[:enables|delivers|impacts*1..5]->(outcome)
        WHERE outcome.node_type IN ['outcome', 'value_driver']

        Args:
            start_node_id: Starting node ID
            max_hops: Maximum traversal depth
            tenant_id: Tenant ID for data isolation

        Returns:
            Dict with paths and outcomes
        """
        if not self._driver:
            return {"paths": [], "outcomes": [], "error": "No database driver"}

        query = """
        MATCH path = (start {id: $start_id, tenant_id: $tenant_id})-[:enables|delivers|impacts|contributesTo|drives*1..$max_hops]->(target)
        WHERE (target:ValueDriver OR target:Outcome OR target:UseCase) AND target.tenant_id = $tenant_id
        RETURN [node in nodes(path) | {id: node.id, name: node.name, type: labels(node)[0]}] as path_nodes,
               [rel in relationships(path) | type(rel)] as path_relationships,
               length(path) as path_length,
               target.id as target_id,
               target.name as target_name
        ORDER BY path_length
        LIMIT 50
        """

        async with self._driver.session() as session:
            result = await session.run(
                query, {"start_id": start_node_id, "max_hops": max_hops, "tenant_id": tenant_id}
            )
            records = [record async for record in result]

        paths = []
        outcomes = set()

        for record in records:
            paths.append(
                {
                    "nodes": record["path_nodes"],
                    "relationships": record["path_relationships"],
                    "length": record["path_length"],
                }
            )
            outcomes.add((record["target_id"], record["target_name"]))

        return {
            "paths": paths,
            "outcomes": [{"id": o[0], "name": o[1]} for o in outcomes],
            "traversal_direction": "upward",
            "start_node": start_node_id,
        }

    async def _downward_traversal(
        self, start_node_id: str, max_hops: int = 5, tenant_id: str = "system"
    ) -> dict[str, Any]:
        """Traverse downward from outcome to capabilities.

        Args:
            start_node_id: Starting node ID (typically ValueDriver or Outcome)
            max_hops: Maximum traversal depth
            tenant_id: Tenant ID for data isolation

        Returns:
            Dict with paths and capabilities
        """
        if not self._driver:
            return {"paths": [], "capabilities": [], "error": "No database driver"}

        query = """
        MATCH path = (start {id: $start_id, tenant_id: $tenant_id})<-[:enables|delivers|impacts|contributesTo|drivenBy|requires*1..$max_hops]-(target)
        WHERE target:Capability AND target.tenant_id = $tenant_id
        RETURN [node in nodes(path) | {id: node.id, name: node.name, type: labels(node)[0]}] as path_nodes,
               [rel in relationships(path) | type(rel)] as path_relationships,
               length(path) as path_length,
               target.id as target_id,
               target.name as target_name
        ORDER BY path_length
        LIMIT 50
        """

        async with self._driver.session() as session:
            result = await session.run(
                query, {"start_id": start_node_id, "max_hops": max_hops, "tenant_id": tenant_id}
            )
            records = [record async for record in result]

        paths = []
        capabilities = set()

        for record in records:
            paths.append(
                {
                    "nodes": record["path_nodes"],
                    "relationships": record["path_relationships"],
                    "length": record["path_length"],
                }
            )
            capabilities.add((record["target_id"], record["target_name"]))

        return {
            "paths": paths,
            "capabilities": [{"id": c[0], "name": c[1]} for c in capabilities],
            "traversal_direction": "downward",
            "start_node": start_node_id,
        }

    async def _semantic_match(
        self, query_text: str, min_confidence: float = 0.7, tenant_id: str = "system"
    ) -> dict[str, Any]:
        """Match query text to value tree nodes using semantic similarity.

        Args:
            query_text: Text to match
            min_confidence: Minimum similarity score
            tenant_id: Tenant ID for data isolation

        Returns:
            Dict with matched nodes and scores
        """
        # Placeholder: In production, this would use embeddings
        # from the vector store to find semantically similar nodes
        logger.info(f"Semantic matching for: {query_text}")

        return {
            "query": query_text,
            "matches": [],  # Would be populated with actual matches
            "min_confidence": min_confidence,
            "note": "Semantic matching requires embedding model integration",
        }

    async def project_pain_point(
        self,
        pain_point_id: str,
        pain_point_description: str,
    ) -> ProjectionResult:
        """Project a pain point onto the value tree.

        This combines semantic matching with upward traversal to find
        relevant value drivers and outcomes.

        Args:
            pain_point_id: ID of the pain point entity
            pain_point_description: Description text for matching

        Returns:
            ProjectionResult with matched nodes and paths
        """
        # Semantic match to find initial nodes
        match_result = await self._semantic_match(pain_point_description, 0.6)

        matched_nodes = []
        match_scores = {}
        traversal_paths = []

        # For each matched node, traverse upward to find outcomes
        for match in match_result.get("matches", []):
            node_id = match.get("id")
            score = match.get("score", 0)

            match_scores[node_id] = score
            matched_nodes.append(match)

            # Traverse upward
            upward = await self._upward_traversal(node_id, max_hops=5)
            traversal_paths.extend(upward.get("paths", []))

        # Calculate overall confidence
        confidence = (
            sum(match_scores.values()) / len(match_scores) if match_scores else 0
        )

        return ProjectionResult(
            projection_id=f"proj-{pain_point_id}",
            pain_point_id=pain_point_id,
            matched_nodes=matched_nodes,
            match_scores=match_scores,
            traversal_path=[
                p["nodes"][-1]["id"] for p in traversal_paths if p.get("nodes")
            ],
            confidence=confidence,
            projection_timestamp=datetime.utcnow().isoformat(),
        )
