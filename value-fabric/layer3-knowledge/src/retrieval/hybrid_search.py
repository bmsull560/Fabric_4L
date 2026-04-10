"""Hybrid search combining BM25, vector similarity, and graph structure.

Changes from original:
- Replaced ``AsyncGraphDatabase.driver()`` with shared ``get_driver()`` factory.
- ``_vector_search``: adapts the new Neo4j VectorStore tuple return format
  ``(entity_id, score, metadata)`` into the dict format expected by
  ``_merge_results``.
- ``_vector_search``: gracefully handles ``None`` vector_store (returns []).
- ``_graph_search``: added null-driver guard.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from neo4j import AsyncDriver

from ..config import Settings, get_settings
from ..db.driver import get_driver
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
    confidence: float
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
        self.settings = settings or get_settings()
        self._driver = driver
        self._owned_driver = driver is None
        self.vector_store = vector_store
        self.graph_engine = graph_engine

    async def _get_driver(self) -> AsyncDriver:
        """Get or create Neo4j driver via the shared singleton factory."""
        if self._driver is None:
            self._driver = await get_driver(self.settings)
        return self._driver

    async def close(self) -> None:
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
        weights = weights or {
            "bm25": self.settings.hybrid_bm25_weight,
            "vector": self.settings.hybrid_vector_weight,
            "graph": self.settings.hybrid_graph_weight,
        }
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        bm25_results = await self._bm25_search(query, entity_types, top_k * 2)
        vector_results = await self._vector_search(query, entity_types, top_k * 2)
        graph_results = await self._graph_search(query, entity_types, top_k * 2)

        merged = self._merge_results(bm25_results, vector_results, graph_results, weights)
        return merged[:top_k]

    async def semantic_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Pure semantic (vector) search."""
        return await self._vector_search(
            query, [entity_type] if entity_type else None, top_k
        )

    async def keyword_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Pure BM25 keyword search."""
        return await self._bm25_search(
            query, [entity_type] if entity_type else None, top_k
        )

    async def fulltext_search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Backward-compatible alias for keyword/BM25 search."""
        return await self.keyword_search(query, entity_type, top_k)

    async def _bm25_search(
        self,
        query: str,
        entity_types: Optional[List[str]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Execute BM25 full-text search via Neo4j fulltext index."""
        driver = await self._get_driver()
        results = []

        if entity_types:
            unions = []
            for etype in entity_types:
                idx = f"{etype.lower()}_fulltext"
                unions.append(
                    f"CALL db.index.fulltext.queryNodes('{idx}', $query) "
                    "YIELD node, score RETURN node, score"
                )
            fulltext_call = "\nUNION\n".join(unions)
        else:
            fulltext_call = """
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
            """

        async with driver.session(database=self.settings.neo4j_database) as session:
            escaped_query = query.replace('"', '\\"')
            cypher = f"""
            CALL {{
                {fulltext_call}
            }}
            WITH node as n, score
            RETURN n.id as id, labels(n)[0] as entity_type, n.name as name,
                   n.description as description, score
            ORDER BY score DESC
            LIMIT $limit
            """
            try:
                result = await session.run(
                    cypher, {"query": escaped_query, "limit": top_k}
                )
                async for record in result:
                    row = dict(record)
                    if entity_types and row.get("entity_type") not in entity_types:
                        continue
                    results.append(row)
            except Exception as exc:
                logger.warning("BM25 search failed: %s", exc)

        return results

    async def _vector_search(
        self,
        query: str,
        entity_types: Optional[List[str]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Execute vector similarity search.

        Adapts the Neo4jVectorStore return format — list of
        ``(entity_id, score, metadata)`` tuples — into the dict format
        expected by ``_merge_results``.
        """
        if not self.vector_store:
            logger.debug("Vector store not configured, skipping vector search")
            return []

        entity_type = entity_types[0] if entity_types else None

        try:
            raw = await self.vector_store.search(
                query_text=query,
                entity_type=entity_type,
                top_k=top_k,
            )
        except Exception as exc:
            logger.warning("Vector search failed: %s", exc)
            return []

        results: List[Dict[str, Any]] = []
        for item in raw:
            # Handle both tuple format (new) and dict format (legacy)
            if isinstance(item, tuple):
                entity_id, score, meta = item
                results.append({
                    "id": entity_id,
                    "entity_id": entity_id,
                    "score": score,
                    "entity_type": meta.get("entity_type", "Unknown"),
                    "name": meta.get("name", ""),
                    "description": meta.get("description", ""),
                    "metadata": meta,
                })
            else:
                # Legacy dict format — ensure 'id' key exists
                item.setdefault("id", item.get("entity_id", ""))
                results.append(item)

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

        if entity_types:
            unions = []
            for etype in entity_types:
                idx = f"{etype.lower()}_fulltext"
                unions.append(
                    f"CALL db.index.fulltext.queryNodes('{idx}', $query) "
                    "YIELD node, score RETURN node, score"
                )
            fulltext_call = "\nUNION\n".join(unions)
        else:
            fulltext_call = """
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
            """

        async with driver.session(database=self.settings.neo4j_database) as session:
            escaped_query = query.replace('"', '\\"')
            cypher = f"""
            CALL {{
                {fulltext_call}
            }}
            WITH node as n, score as text_score
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
            except Exception as exc:
                logger.warning("Graph search failed: %s", exc)

        return results

    def _merge_results(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        graph_results: List[Dict],
        weights: Dict[str, float],
    ) -> List[HybridSearchResult]:
        """Merge and rank results from multiple sources."""
        all_ids: set = set()
        bm25_lookup: Dict[str, Dict] = {}
        vector_lookup: Dict[str, Dict] = {}
        graph_lookup: Dict[str, Dict] = {}

        for r in bm25_results:
            eid = r.get("id") or r.get("entity_id")
            if eid:
                all_ids.add(eid)
                bm25_lookup[eid] = r

        for r in vector_results:
            eid = r.get("id") or r.get("entity_id")
            if eid:
                all_ids.add(eid)
                vector_lookup[eid] = r

        for r in graph_results:
            eid = r.get("id")
            if eid:
                all_ids.add(eid)
                graph_lookup[eid] = r

        bm25_max = max((r.get("score", 0.0) for r in bm25_results), default=1.0) or 1.0
        vector_max = max((r.get("score", 0.0) for r in vector_results), default=1.0) or 1.0
        graph_max = max((r.get("score", 0.0) for r in graph_results), default=1.0) or 1.0

        merged = []
        for entity_id in all_ids:
            bm25_score = bm25_lookup.get(entity_id, {}).get("score", 0.0) / bm25_max
            vector_score = vector_lookup.get(entity_id, {}).get("score", 0.0) / vector_max
            graph_score = graph_lookup.get(entity_id, {}).get("score", 0.0) / graph_max

            combined = (
                weights["bm25"] * bm25_score
                + weights["vector"] * vector_score
                + weights["graph"] * graph_score
            )

            source = (
                bm25_lookup.get(entity_id)
                or vector_lookup.get(entity_id)
                or graph_lookup.get(entity_id)
                or {}
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
                    confidence=combined,
                    metadata=source.get("metadata", {}),
                )
            )

        merged.sort(key=lambda x: x.combined_score, reverse=True)
        return merged
