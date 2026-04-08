"""Hybrid search combining BM25, vector similarity, and graph structure."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from neo4j import AsyncDriver, AsyncGraphDatabase

from ..config import Settings, get_settings
from .graph_rag import GraphRAGEngine
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Result from hybrid search."""

    entity_id: str
    entity_type: str
    name: str
    bm25_score: float
    vector_score: float
    graph_score: float
    combined_score: float
    metadata: Dict[str, Any]


class HybridSearch:
    """Hybrid search engine combining multiple retrieval signals.

    Combines:
    1. BM25 sparse retrieval (full-text search)
    2. Dense vector similarity (semantic search)
    3. Graph centrality/pagerank (structural importance)
    4. Recency boost (for temporal relevance)
    """

    def __init__(
        self,
        driver: Optional[AsyncDriver] = None,
        vector_store: Optional[VectorStore] = None,
        graph_engine: Optional[GraphRAGEngine] = None,
        settings: Optional[Settings] = None,
    ):
        """Initialize hybrid search.

        Args:
            driver: Neo4j async driver
            vector_store: Vector store for semantic search
            graph_engine: GraphRAG engine for graph traversal
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self._driver = driver
        self._owned_driver = driver is None
        self.vector_store = vector_store
        self.graph_engine = graph_engine

    async def _get_driver(self) -> AsyncDriver:
        """Get or create Neo4j driver."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=self.settings.neo4j_auth,
                max_connection_pool_size=self.settings.neo4j_max_pool_size,
            )
        return self._driver

    async def close(self) -> None:
        """Close Neo4j driver if owned."""
        if self._owned_driver and self._driver:
            await self._driver.close()
            self._driver = None

    async def search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        top_k: int = 10,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[HybridSearchResult]:
        """Execute hybrid search across all signals.

        Args:
            query: Search query text
            entity_types: Filter by entity types
            top_k: Number of results to return
            weights: Custom weights for bm25, vector, graph

        Returns:
            List of ranked search results
        """
        # Use configured weights if not provided
        weights = weights or {
            "bm25": self.settings.hybrid_bm25_weight,
            "vector": self.settings.hybrid_vector_weight,
            "graph": self.settings.hybrid_graph_weight,
        }

        # Normalize weights
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        # Run searches in parallel where possible
        bm25_results = await self._bm25_search(query, entity_types, top_k * 2)
        vector_results = await self._vector_search(query, entity_types, top_k * 2)
        graph_results = await self._graph_search(query, entity_types, top_k * 2)

        # Merge and score results
        merged = self._merge_results(
            bm25_results, vector_results, graph_results, weights
        )

        # Return top_k
        return merged[:top_k]

    async def semantic_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 10,
    ) -> List[HybridSearchResult]:
        """Pure semantic search using vector similarity.

        Args:
            query: Search query
            entity_type: Filter by entity type
            top_k: Number of results

        Returns:
            List of search results
        """
        vector_results = await self._vector_search(query, [entity_type] if entity_type else None, top_k)

        return [
            HybridSearchResult(
                entity_id=r["id"],
                entity_type=r.get("entity_type", "Unknown"),
                name=r.get("text", "")[:100],
                bm25_score=0.0,
                vector_score=r["score"],
                graph_score=0.0,
                combined_score=r["score"],
                metadata=r.get("metadata", {}),
            )
            for r in vector_results
        ]

    async def fulltext_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 10,
    ) -> List[HybridSearchResult]:
        """Pure full-text search using BM25.

        Args:
            query: Search query
            entity_type: Filter by entity type
            top_k: Number of results

        Returns:
            List of search results
        """
        bm25_results = await self._bm25_search(query, [entity_type] if entity_type else None, top_k)

        return [
            HybridSearchResult(
                entity_id=r["id"],
                entity_type=r["entity_type"],
                name=r["name"],
                bm25_score=r["score"],
                vector_score=0.0,
                graph_score=0.0,
                combined_score=r["score"],
                metadata=r.get("metadata", {}),
            )
            for r in bm25_results
        ]

    async def _bm25_search(
        self,
        query: str,
        entity_types: Optional[List[str]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Execute BM25 full-text search via Neo4j."""
        driver = await self._get_driver()
        results = []

        # Escape special characters in query
        escaped_query = query.replace('"', '\\"')

        async with driver.session(database=self.settings.neo4j_database) as session:
            if entity_types and len(entity_types) == 1:
                # Search specific index
                index_name = f"{entity_types[0].lower()}_fulltext"
                cypher = f"""
                CALL db.index.fulltext.queryNodes('{index_name}', $query)
                YIELD node, score
                RETURN node.id as id, labels(node)[0] as entity_type, 
                       node.name as name, score
                LIMIT $limit
                """
                result = await session.run(
                    cypher, {"query": escaped_query, "limit": top_k}
                )
                async for record in result:
                    results.append(dict(record))

            else:
                # Search across all indexes
                all_indexes = [
                    "capability_fulltext",
                    "usecase_fulltext",
                    "persona_fulltext",
                    "valuedriver_fulltext",
                ]

                for index_name in all_indexes:
                    try:
                        result = await session.run(
                            f"""
                            CALL db.index.fulltext.queryNodes('{index_name}', $query)
                            YIELD node, score
                            RETURN node.id as id, labels(node)[0] as entity_type,
                                   node.name as name, score
                            LIMIT $limit
                            """,
                            {"query": escaped_query, "limit": top_k},
                        )
                        async for record in result:
                            if not entity_types or record["entity_type"] in entity_types:
                                results.append(dict(record))
                    except Exception as e:
                        logger.warning(f"Fulltext search failed for {index_name}: {e}")

        # Sort by score and deduplicate
        results.sort(key=lambda x: x["score"], reverse=True)
        seen_ids = set()
        unique_results = []
        for r in results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                unique_results.append(r)

        return unique_results[:top_k]

    async def _vector_search(
        self,
        query: str,
        entity_types: Optional[List[str]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Execute vector similarity search."""
        if not self.vector_store:
            logger.warning("Vector store not available, skipping vector search")
            return []

        # Use first entity type if specified, or None for all
        entity_type = entity_types[0] if entity_types else None

        results = await self.vector_store.search(
            query=query,
            entity_type=entity_type,
            top_k=top_k,
        )

        # Add ID field for consistency
        for r in results:
            r["id"] = r["entity_id"]

        return results

    async def _graph_search(
        self,
        query: str,
        entity_types: Optional[List[str]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Execute graph-based search (centrality-aware)."""
        driver = await self._get_driver()
        results = []

        # First find relevant entities via text search, then rank by graph centrality
        async with driver.session(database=self.settings.neo4j_database) as session:
            # Get candidate entities via fulltext
            escaped_query = query.replace('"', '\\"')

            entity_filter = ""
            if entity_types:
                labels = "|".join(entity_types)
                entity_filter = f"AND ANY(label IN labels(n) WHERE label IN {entity_types})"

            # Rank by PageRank / centrality
            cypher = f"""
            CALL db.index.fulltext.queryNodes('capability_fulltext', $query)
            YIELD node as n, score as text_score
            {entity_filter}
            WITH n, text_score
            OPTIONAL MATCH (n)-[r]-()
            WITH n, text_score, count(r) as degree
            RETURN n.id as id, labels(n)[0] as entity_type, n.name as name,
                   text_score * log(degree + 1) as score
            ORDER BY score DESC
            LIMIT $limit
            """

            try:
                result = await session.run(
                    cypher, {"query": escaped_query, "limit": top_k}
                )
                async for record in result:
                    results.append(dict(record))
            except Exception as e:
                logger.warning(f"Graph search failed: {e}")

        return results

    def _merge_results(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        graph_results: List[Dict],
        weights: Dict[str, float],
    ) -> List[HybridSearchResult]:
        """Merge and rank results from multiple sources."""
        # Create lookup dictionaries
        all_ids = set()
        bm25_lookup = {}
        vector_lookup = {}
        graph_lookup = {}

        for r in bm25_results:
            entity_id = r["id"]
            all_ids.add(entity_id)
            bm25_lookup[entity_id] = r

        for r in vector_results:
            entity_id = r["id"]
            all_ids.add(entity_id)
            vector_lookup[entity_id] = r

        for r in graph_results:
            entity_id = r.get("id")
            if entity_id:
                all_ids.add(entity_id)
                graph_lookup[entity_id] = r

        # Merge and score
        merged = []
        for entity_id in all_ids:
            # Get scores from each source (default to 0 if not found)
            bm25_score = bm25_lookup.get(entity_id, {}).get("score", 0.0)
            vector_score = vector_lookup.get(entity_id, {}).get("score", 0.0)
            graph_score = graph_lookup.get(entity_id, {}).get("score", 0.0)

            # Normalize scores to 0-1 range (min-max normalization within each list)
            if bm25_results:
                bm25_max = max(r["score"] for r in bm25_results) or 1.0
                bm25_score = bm25_score / bm25_max

            if vector_results:
                vector_max = max(r["score"] for r in vector_results) or 1.0
                vector_score = vector_score / vector_max

            if graph_results:
                graph_max = max(r["score"] for r in graph_results) or 1.0
                graph_score = graph_score / graph_max

            # Calculate combined score
            combined = (
                weights["bm25"] * bm25_score +
                weights["vector"] * vector_score +
                weights["graph"] * graph_score
            )

            # Get entity metadata from any available source
            source = (
                bm25_lookup.get(entity_id) or
                vector_lookup.get(entity_id) or
                graph_lookup.get(entity_id) or
                {}
            )

            merged.append(
                HybridSearchResult(
                    entity_id=entity_id,
                    entity_type=source.get("entity_type", "Unknown"),
                    name=source.get("name", source.get("text", "")[:100]),
                    bm25_score=bm25_score,
                    vector_score=vector_score,
                    graph_score=graph_score,
                    combined_score=combined,
                    metadata=source.get("metadata", {}),
                )
            )

        # Sort by combined score
        merged.sort(key=lambda x: x.combined_score, reverse=True)

        return merged
