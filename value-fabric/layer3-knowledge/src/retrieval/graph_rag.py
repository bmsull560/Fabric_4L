"""GraphRAG retrieval engine for multi-hop traversal."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from neo4j import AsyncDriver

from ..config import Settings, get_settings
from ..db.driver import get_driver
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class GraphRAGResult:
    """Result from a GraphRAG query."""

    query: str
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    context_graph: Dict[str, Any]
    traversal_path: List[str]
    confidence_score: float
    sources: List[str]


class GraphRAGEngine:
    """GraphRAG engine for contextual retrieval from Knowledge Graph.

    Combines vector similarity with graph traversal to find
    relevant entities and their multi-hop neighborhoods.
    """

    def __init__(
        self,
        driver: Optional[AsyncDriver] = None,
        vector_store: Optional[VectorStore] = None,
        settings: Optional[Settings] = None,
    ):
        """Initialize GraphRAG engine.

        Args:
            driver: Neo4j async driver
            vector_store: Vector store for semantic search
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self._driver = driver
        self._owned_driver = driver is None
        self.vector_store = vector_store

    async def _get_driver(self) -> AsyncDriver:
        """Get or create Neo4j driver via the shared singleton factory."""
        if self._driver is None:
            self._driver = await get_driver(self.settings)
        return self._driver

    async def close(self) -> None:
        """Close Neo4j driver if owned."""
        if self._owned_driver and self._driver:
            await self._driver.close()
            self._driver = None

    async def query(
        self,
        query_text: str,
        entity_type: Optional[str] = None,
        max_hops: Optional[int] = None,
        min_confidence: Optional[float] = None,
        max_results: int = 10,
    ) -> GraphRAGResult:
        """Execute a GraphRAG query.

        Args:
            query_text: Natural language query
            entity_type: Filter by entity type
            max_hops: Maximum graph traversal hops
            min_confidence: Minimum confidence threshold
            max_results: Maximum number of results to return

        Returns:
            GraphRAGResult with entities, relationships, and context
        """
        max_hops = max_hops or self.settings.graphrag_max_hops
        min_confidence = min_confidence or self.settings.graphrag_min_confidence

        # Step 1: Find seed entities via vector search
        seed_entities = await self._find_seed_entities(
            query_text, entity_type, max_results
        )

        if not seed_entities:
            logger.warning(f"No seed entities found for query: {query_text}")
            return GraphRAGResult(
                query=query_text,
                entities=[],
                relationships=[],
                context_graph={},
                traversal_path=[],
                confidence_score=0.0,
                sources=[],
            )

        # Step 2: Expand context via graph traversal
        expanded_context = await self._expand_context(
            seed_entities, max_hops, min_confidence
        )

        # Step 3: Build result
        result = self._build_result(query_text, seed_entities, expanded_context)

        return result

    async def get_entity_context(
        self,
        entity_id: str,
        hops: int = 2,
        relationship_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get the neighborhood context around an entity.

        Args:
            entity_id: Entity ID to center on
            hops: Number of hops to traverse
            relationship_types: Filter by relationship types

        Returns:
            Context dictionary with entities and relationships
        """
        driver = await self._get_driver()

        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_list = "|".join(f"`{r}`" for r in relationship_types)
            rel_filter = f"AND type(r) IN [{', '.join(f"'{r}'" for r in relationship_types)}]"

        query = f"""
        MATCH path = (center {{id: $entity_id}})-[r*1..{hops}]-(connected)
        WHERE ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
        {rel_filter}
        WITH center, 
             collect(DISTINCT connected) as neighbors,
             collect(DISTINCT {{rel: r, nodes: nodes(path)}}) as paths
        RETURN center, neighbors, paths
        """

        async with driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                query,
                {
                    "entity_id": entity_id,
                    "min_confidence": self.settings.graphrag_min_confidence,
                },
            )
            record = await result.single()

            if not record:
                return {"center": None, "neighbors": [], "relationships": []}

            center = dict(record["center"])
            neighbors = [dict(n) for n in record["neighbors"]]

            # Extract relationships from paths
            relationships = []
            for path_info in record["paths"]:
                rels = path_info["rel"]
                if isinstance(rels, list):
                    for rel in rels:
                        relationships.append({
                            "type": rel.type,
                            "source": rel.start_node["id"],
                            "target": rel.end_node["id"],
                            "properties": dict(rel),
                        })

            return {
                "center": center,
                "neighbors": neighbors,
                "relationships": relationships,
                "entity_count": 1 + len(neighbors),
                "relationship_count": len(relationships),
            }

    async def traverse_value_tree(
        self,
        start_entity_id: str,
        direction: str = "both",  # up, down, both
    ) -> Dict[str, Any]:
        """Traverse the 4-layer value tree from a starting entity.

        Args:
            start_entity_id: Entity ID to start from
            direction: Tree traversal direction (up=to ValueDriver, down=to Capability)

        Returns:
            Value tree paths from the starting entity
        """
        driver = await self._get_driver()

        # Define traversal patterns based on the 4-layer ontology
        # Capability -> ENABLES -> UseCase -> BENEFITS -> Persona -> DRIVES -> ValueDriver
        if direction == "up":
            # Towards ValueDriver (outgoing relationships)
            query = """
            MATCH path = (start {id: $entity_id})-[:ENABLES|BENEFITS|DRIVES|CONTRIBUTES_TO*1..5]->(end)
            WHERE ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
            RETURN nodes(path) as nodes, relationships(path) as rels
            """
        elif direction == "down":
            # Towards Capability (incoming relationships)
            query = """
            MATCH path = (end)<-[:ENABLES|BENEFITS|DRIVES|CONTRIBUTES_TO*1..5]-(start {id: $entity_id})
            WHERE ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
            RETURN nodes(path) as nodes, relationships(path) as rels
            """
        else:
            # Both directions
            query = """
            MATCH path = (start {id: $entity_id})-[:ENABLES|BENEFITS|DRIVES|CONTRIBUTES_TO|REQUIRES|DEPENDS_ON*1..5]-(end)
            WHERE start <> end
              AND ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
            RETURN nodes(path) as nodes, relationships(path) as rels, start as start_node
            """

        async with driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                query,
                {
                    "entity_id": start_entity_id,
                    "min_confidence": self.settings.graphrag_min_confidence,
                },
            )

            paths = []
            async for record in result:
                nodes = [dict(n) for n in record["nodes"]]
                rels = record["rels"]

                # Convert relationships
                relationships = []
                for rel in rels:
                    relationships.append({
                        "type": rel.type,
                        "source": rel.start_node["id"],
                        "target": rel.end_node["id"],
                        "properties": dict(rel),
                    })

                paths.append({"nodes": nodes, "relationships": relationships})

            return {
                "start_entity_id": start_entity_id,
                "direction": direction,
                "paths": paths,
                "path_count": len(paths),
            }

    async def _find_seed_entities(
        self,
        query_text: str,
        entity_type: Optional[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """Find seed entities using vector search."""
        if not self.vector_store:
            # Fallback to Neo4j full-text search
            return await self._fulltext_search(query_text, entity_type, max_results)

        # Use vector store for semantic search
        # New VectorStore.search() uses query_text= kwarg and returns tuples
        raw_results = await self.vector_store.search(
            query_text=query_text,
            entity_type=entity_type,
            top_k=max_results,
        )
        # Normalise: new VectorStore returns (entity_id, score, meta) tuples
        results = []
        for item in raw_results:
            if isinstance(item, tuple):
                entity_id, score, meta = item
                results.append({"id": entity_id, "score": score, **meta})
            else:
                item.setdefault("id", item.get("entity_id", ""))
                results.append(item)

        # Enrich with full entity data from Neo4j
        driver = await self._get_driver()
        enriched_results = []

        async with driver.session(database=self.settings.neo4j_database) as session:
            for result in results:
                entity_result = await session.run(
                    "MATCH (n {id: $entity_id}) RETURN n",
                    {"entity_id": result["id"]},
                )
                record = await entity_result.single()

                if record:
                    entity_data = dict(record["n"])
                    entity_data["vector_score"] = result.get("score", 0.0)
                    enriched_results.append(entity_data)
        return enriched_results

    async def _fulltext_search(
        self,
        query_text: str,
        entity_type: Optional[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        """Fallback full-text search using Neo4j indexes."""
        driver = await self._get_driver()

        if entity_type:
            # Search specific entity type
            query = f"""
            CALL db.index.fulltext.queryNodes('{entity_type.lower()}_fulltext', $query)
            YIELD node, score
            RETURN node, score
            LIMIT $limit
            """
        else:
            # Search across all entity types
            query = """
            CALL {
                CALL db.index.fulltext.queryNodes('capability_fulltext', $query)
                YIELD node, score RETURN node, score
                UNION
                CALL db.index.fulltext.queryNodes('usecase_fulltext', $query)
                YIELD node, score RETURN node, score
                UNION
                CALL db.index.fulltext.queryNodes('persona_fulltext', $query)
                YIELD node, score RETURN node, score
                UNION
                CALL db.index.fulltext.queryNodes('valuedriver_fulltext', $query)
                YIELD node, score RETURN node, score
            }
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """

        async with driver.session(database=self.settings.neo4j_database) as session:
            result = await session.run(
                query,
                {"query": query_text, "limit": max_results},
            )

            entities = []
            async for record in result:
                entity_data = dict(record["node"])
                entity_data["text_score"] = record["score"]
                entities.append(entity_data)

            return entities

    async def _expand_context(
        self,
        seed_entities: List[Dict[str, Any]],
        max_hops: int,
        min_confidence: float,
    ) -> Dict[str, Any]:
        """Expand context via graph traversal from seed entities."""
        driver = await self._get_driver()

        seed_ids = [e["id"] for e in seed_entities]
        all_entities: Dict[str, Dict] = {e["id"]: e for e in seed_entities}
        all_relationships: List[Dict] = []
        traversal_path: List[str] = []

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Find connected entities within max_hops
            query = f"""
            MATCH path = (seed)-[r*1..{max_hops}]-(connected)
            WHERE seed.id IN $seed_ids
              AND ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
            RETURN seed.id as seed_id, 
                   nodes(path) as path_nodes,
                   relationships(path) as path_rels,
                   length(path) as hops
            LIMIT $max_nodes
            """

            result = await session.run(
                query,
                {
                    "seed_ids": seed_ids,
                    "min_confidence": min_confidence,
                    "max_nodes": self.settings.graphrag_max_nodes,
                },
            )

            async for record in result:
                # Add entities
                for node in record["path_nodes"]:
                    node_id = node["id"]
                    if node_id not in all_entities:
                        all_entities[node_id] = dict(node)
                        all_entities[node_id]["hops_from_seed"] = record["hops"]

                # Add relationships
                for rel in record["path_rels"]:
                    rel_data = {
                        "type": rel.type,
                        "source": rel.start_node["id"],
                        "target": rel.end_node["id"],
                        "properties": dict(rel),
                        "hops": record["hops"],
                    }
                    if rel_data not in all_relationships:
                        all_relationships.append(rel_data)

                # Track traversal path
                path_str = f"{record['seed_id']} -> {record['hops']} hops"
                if path_str not in traversal_path:
                    traversal_path.append(path_str)

        return {
            "entities": list(all_entities.values()),
            "relationships": all_relationships,
            "traversal_path": traversal_path,
            "seed_count": len(seed_entities),
            "expanded_count": len(all_entities) - len(seed_entities),
        }

    def _build_result(
        self,
        query: str,
        seed_entities: List[Dict],
        expanded_context: Dict,
    ) -> GraphRAGResult:
        """Build final GraphRAG result."""
        # Calculate confidence score based on entity confidence and vector scores
        confidences = []
        for entity in expanded_context["entities"]:
            entity_conf = entity.get("confidence", 0.5)
            vector_score = entity.get("vector_score", 0.5)
            # Combine scores
            combined = 0.6 * entity_conf + 0.4 * vector_score
            confidences.append(combined)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Extract sources
        sources = list(
            set(
                e.get("source_id")
                for e in expanded_context["entities"]
                if e.get("source_id")
            )
        )

        return GraphRAGResult(
            query=query,
            entities=expanded_context["entities"],
            relationships=expanded_context["relationships"],
            context_graph={
                "node_count": len(expanded_context["entities"]),
                "edge_count": len(expanded_context["relationships"]),
                "seed_nodes": [e["id"] for e in seed_entities],
            },
            traversal_path=expanded_context["traversal_path"],
            confidence_score=avg_confidence,
            sources=sources,
        )
