"""GraphRAG retrieval engine for multi-hop traversal."""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from neo4j import AsyncDriver
from neo4j.time import Date as Neo4jDate
from neo4j.time import DateTime as Neo4jDateTime

from ..config import Settings, get_settings
from ..db.driver import get_driver
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


def _serialize_neo4j_value(value: Any) -> Any:
    """Serialize Neo4j temporal types and other non-JSON types to JSON-serializable formats.

    Args:
        value: Any value from Neo4j node properties

    Returns:
        JSON-serializable value
    """
    if isinstance(value, Neo4jDateTime) or isinstance(value, Neo4jDate):
        return value.to_native().isoformat()
    elif isinstance(value, datetime) or isinstance(value, date):
        return value.isoformat()
    elif isinstance(value, list):
        return [_serialize_neo4j_value(item) for item in value]
    elif isinstance(value, dict):
        return {k: _serialize_neo4j_value(v) for k, v in value.items()}
    return value


def _serialize_entity(entity: dict[str, Any]) -> dict[str, Any]:
    """Serialize an entity dict, converting Neo4j temporal types to strings.

    Adds backward-compatible alias fields for frontend contract alignment:
    - 'name' alias for 'label' or 'name'
    - 'entity_type' alias for 'type' or first label
    - 'confidence_score' alias for 'confidence'

    Args:
        entity: Entity dictionary from Neo4j

    Returns:
        JSON-serializable entity dictionary with alias fields
    """
    # Base serialization of Neo4j values
    serialized = {k: _serialize_neo4j_value(v) for k, v in entity.items()}

    # ═════════════════════════════════════════════════════════════════════════
    # Backward-compatible alias fields for frontend contract alignment
    # ═════════════════════════════════════════════════════════════════════════

    # Add 'name' alias (prefer 'label', fallback to 'name')
    if "name" not in serialized:
        if "label" in serialized:
            serialized["name"] = serialized["label"]
        elif "name" in entity:
            serialized["name"] = entity["name"]

    # Add 'entity_type' alias (prefer 'type', fallback to first label)
    if "entity_type" not in serialized:
        if "type" in serialized:
            serialized["entity_type"] = serialized["type"]
        elif "labels" in serialized and serialized["labels"]:
            # Use first label as entity type
            serialized["entity_type"] = serialized["labels"][0]

    # Add 'confidence_score' alias (from 'confidence')
    if "confidence_score" not in serialized and "confidence" in serialized:
        serialized["confidence_score"] = serialized["confidence"]

    return serialized


def _serialize_relationship(rel: Any, include_hops: bool = False, hops: int = 0) -> dict[str, Any]:
    """Serialize a Neo4j relationship with alias fields.

    Centralizes relationship serialization to ensure consistent alias field
    handling across all GraphRAG query paths.

    Args:
        rel: Neo4j relationship object
        include_hops: Whether to include hops count in output
        hops: Number of hops (only included if include_hops=True)

    Returns:
        JSON-serializable relationship dictionary with alias fields
    """
    data: dict[str, Any] = {
        "type": rel.type,
        "relationship_type": rel.type,  # Frontend alias
        "source": rel.start_node["id"],
        "target": rel.end_node["id"],
        "properties": _serialize_entity(dict(rel)),
    }
    if include_hops:
        data["hops"] = hops
    return data


@dataclass
class GraphRAGResult:
    """Result from a GraphRAG query."""

    query: str
    entities: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    context_graph: dict[str, Any]
    traversal_path: list[str]
    confidence_score: float
    sources: list[str]


class GraphRAGEngine:
    """GraphRAG engine for contextual retrieval from Knowledge Graph.

    Combines vector similarity with graph traversal to find
    relevant entities and their multi-hop neighborhoods.
    """

    def __init__(
        self,
        driver: AsyncDriver | None = None,
        vector_store: VectorStore | None = None,
        settings: Settings | None = None,
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
        entity_type: str | None = None,
        max_hops: int | None = None,
        min_confidence: float | None = None,
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
        relationship_types: list[str] | None = None,
    ) -> dict[str, Any]:
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
            "|".join(f"`{r}`" for r in relationship_types)
            rel_types_str = ", ".join(f"'{r}'" for r in relationship_types)
            rel_filter = f"AND type(r) IN [{rel_types_str}]"

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

            center = _serialize_entity(dict(record["center"]))
            neighbors = [_serialize_entity(dict(n)) for n in record["neighbors"]]

            # Extract relationships from paths
            relationships = []
            for path_info in record["paths"]:
                rels = path_info["rel"]
                if isinstance(rels, list):
                    for rel in rels:
                        relationships.append(_serialize_relationship(rel))

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
    ) -> dict[str, Any]:
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
                nodes = [_serialize_entity(dict(n)) for n in record["nodes"]]
                rels = record["rels"]

                # Convert relationships
                relationships = []
                for rel in rels:
                    relationships.append(_serialize_relationship(rel))

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
        entity_type: str | None,
        max_results: int,
    ) -> list[dict[str, Any]]:
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
                    entity_data = _serialize_entity(dict(record["n"]))
                    entity_data["vector_score"] = result.get("score", 0.0)
                    enriched_results.append(entity_data)
        return enriched_results

    async def _fulltext_search(
        self,
        query_text: str,
        entity_type: str | None,
        max_results: int,
    ) -> list[dict[str, Any]]:
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
                entity_data = _serialize_entity(dict(record["node"]))
                entity_data["text_score"] = record["score"]
                entities.append(entity_data)

            return entities

    async def _expand_context(
        self,
        seed_entities: list[dict[str, Any]],
        max_hops: int,
        min_confidence: float,
    ) -> dict[str, Any]:
        """Expand context via graph traversal from seed entities."""
        driver = await self._get_driver()

        seed_ids = [e["id"] for e in seed_entities]
        all_entities: dict[str, dict] = {e["id"]: e for e in seed_entities}
        all_relationships: list[dict] = []
        traversal_path: list[str] = []

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
                        all_entities[node_id] = _serialize_entity(dict(node))
                        all_entities[node_id]["hops_from_seed"] = record["hops"]

                # Add relationships
                for rel in record["path_rels"]:
                    rel_data = _serialize_relationship(
                        rel, include_hops=True, hops=record["hops"]
                    )
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
        seed_entities: list[dict],
        expanded_context: dict,
    ) -> GraphRAGResult:
        """Build final GraphRAG result."""
        # Calculate confidence score based on entity confidence and vector scores
        confidences = []
        for entity in expanded_context["entities"]:
            entity_conf = float(entity.get("confidence", 0.5))
            vector_score = float(entity.get("vector_score", 0.5))
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

    # Progress calculation constants for streaming
    _PROGRESS_START = 0.0
    _PROGRESS_SEED_BEGIN = 5.0
    _PROGRESS_SEED_RANGE = 20.0  # Seeds fill 5% -> 25%
    _PROGRESS_HOPS_BEGIN = 25.0
    _PROGRESS_HOPS_RANGE = 50.0  # Hops fill 25% -> 75%
    _PROGRESS_RESULT = 95.0
    _PROGRESS_COMPLETE = 100.0

    async def query_stream(
        self,
        query_text: str,
        entity_type: str | None = None,
        max_hops: int | None = None,
        min_confidence: float | None = None,
        max_results: int = 10,
    ):
        """Execute a streaming GraphRAG query.

        Yields progressive results as they are discovered:
        1. Start event
        2. Seed entities as found
        3. Context nodes and edges during traversal
        4. Progress updates
        5. Final result
        6. Complete event

        Args:
            query_text: Natural language query
            entity_type: Filter by entity type
            max_hops: Maximum graph traversal hops
            min_confidence: Minimum confidence threshold
            max_results: Maximum number of results to return

        Yields:
            Dict representing streaming event with event_type and data
        """
        max_hops = max(max_hops or self.settings.graphrag_max_hops, 1)  # Ensure >= 1
        min_confidence = min_confidence or self.settings.graphrag_min_confidence

        # Start event
        yield {
            "event_type": "start",
            "data": {
                "query": query_text,
                "max_hops": max_hops,
                "entity_type": entity_type,
            },
            "progress_percent": self._PROGRESS_START,
        }

        # Step 1: Find seed entities via vector search (25% of progress)
        seed_entities = await self._find_seed_entities(
            query_text, entity_type, max_results
        )

        if not seed_entities:
            yield {
                "event_type": "error",
                "data": {"message": f"No seed entities found for query: {query_text}"},
                "progress_percent": self._PROGRESS_COMPLETE,
            }
            yield {
                "event_type": "complete",
                "data": {"entities_found": 0, "relationships_found": 0},
                "progress_percent": self._PROGRESS_COMPLETE,
            }
            return

        # Yield seed entities
        seed_count = len(seed_entities)
        for i, entity in enumerate(seed_entities):
            progress = (
                self._PROGRESS_SEED_BEGIN + (i / seed_count) * self._PROGRESS_SEED_RANGE
            )
            yield {
                "event_type": "seed_entity",
                "data": {"entity": entity, "index": i, "total": seed_count},
                "progress_percent": progress,
            }

        # Step 2: Stream context expansion hop by hop (50% of progress)
        seed_ids = [e["id"] for e in seed_entities]
        all_entities: dict[str, dict] = {e["id"]: e for e in seed_entities}
        all_relationships: list[dict] = []
        traversal_path: list[str] = []

        driver = await self._get_driver()

        async with driver.session(database=self.settings.neo4j_database) as session:
            # Process one hop at a time for progressive streaming
            for current_hop in range(1, max_hops + 1):
                hop_query = f"""
                MATCH path = (seed)-[r*1..{current_hop}]-(connected)
                WHERE seed.id IN $seed_ids
                  AND length(path) = {current_hop}
                  AND ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
                  AND connected.id NOT IN $existing_ids
                RETURN nodes(path) as path_nodes,
                       relationships(path) as path_rels,
                       length(path) as hops
                LIMIT $max_nodes
                """

                # Avoid division by zero - distribute max_nodes across hops evenly
                nodes_per_hop = max(self.settings.graphrag_max_nodes // max_hops, 1)

                result = await session.run(
                    hop_query,
                    {
                        "seed_ids": seed_ids,
                        "existing_ids": list(all_entities.keys()),
                        "min_confidence": min_confidence,
                        "max_nodes": nodes_per_hop,
                    },
                )

                hop_entities = []
                hop_relationships = []

                async for record in result:
                    # Add entities
                    for node in record["path_nodes"]:
                        node_id = node["id"]
                        if node_id not in all_entities:
                            entity_data = _serialize_entity(dict(node))
                            entity_data["hops_from_seed"] = record["hops"]
                            all_entities[node_id] = entity_data
                            hop_entities.append(entity_data)

                    # Add relationships
                    for rel in record["path_rels"]:
                        rel_data = _serialize_relationship(
                            rel, include_hops=True, hops=record["hops"]
                        )
                        if rel_data not in all_relationships:
                            all_relationships.append(rel_data)
                            hop_relationships.append(rel_data)

                # Stream hop results with progress based on current hop
                hop_progress = (current_hop / max_hops) * self._PROGRESS_HOPS_RANGE
                progress_base = self._PROGRESS_HOPS_BEGIN + hop_progress

                for entity in hop_entities:
                    yield {
                        "event_type": "context_node",
                        "data": {"entity": entity, "hop": current_hop},
                        "progress_percent": progress_base,
                    }

                for rel in hop_relationships:
                    yield {
                        "event_type": "context_edge",
                        "data": {"relationship": rel, "hop": current_hop},
                        "progress_percent": progress_base,
                    }

                # Progress update
                next_hop_progress = (
                    (current_hop + 1) / max_hops
                ) * self._PROGRESS_HOPS_RANGE
                yield {
                    "event_type": "progress",
                    "data": {
                        "hop": current_hop,
                        "total_hops": max_hops,
                        "entities_found": len(all_entities),
                        "relationships_found": len(all_relationships),
                    },
                    "progress_percent": self._PROGRESS_HOPS_BEGIN + next_hop_progress,
                }

        # Build final result
        final_result = self._build_result(
            query_text,
            seed_entities,
            {
                "entities": list(all_entities.values()),
                "relationships": all_relationships,
                "traversal_path": traversal_path,
                "seed_count": len(seed_entities),
                "expanded_count": len(all_entities) - len(seed_entities),
            },
        )

        # Result event
        yield {
            "event_type": "result",
            "data": {
                "query": final_result.query,
                "confidence_score": final_result.confidence_score,
                "entity_count": len(final_result.entities),
                "relationship_count": len(final_result.relationships),
                "sources": final_result.sources,
            },
            "progress_percent": self._PROGRESS_RESULT,
        }

        # Complete event
        yield {
            "event_type": "complete",
            "data": {
                "entities_found": len(all_entities),
                "relationships_found": len(all_relationships),
                "hops_traversed": max_hops,
            },
            "progress_percent": self._PROGRESS_COMPLETE,
        }
