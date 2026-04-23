"""
Neo4j-native vector store for entity embeddings.

Replaces the previous Pinecone-based implementation.  Uses Neo4j 5.x
vector indexes (``CREATE VECTOR INDEX``) with ``db.index.vector.queryNodes``
for ANN search.  No external vector database required.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast)
or text-embedding-3-small compatible (1536-dim).  Dimension is read from
config so it can be changed without code changes.

Design notes:
- Embeddings are stored as a Float[] property on each entity node.
- The vector index is created by SchemaInitializer at startup.
- This class is stateless with respect to the driver — it accepts an
  injected driver so it can be tested with a testcontainers Neo4j instance.
- Pinecone dependency has been removed from pyproject.toml.
"""

import logging
from typing import Any

from neo4j import AsyncDriver
from neo4j.exceptions import ClientError, ServiceUnavailable

from ..config import Settings, get_settings
from ..db.driver import get_driver

logger = logging.getLogger(__name__)

# Supported entity types for vector search
VECTOR_ENTITY_TYPES = ["Capability", "UseCase", "Persona", "ValueDriver"]


class VectorStoreError(Exception):
    """Raised when a vector store operation fails."""


class Neo4jVectorStore:
    """Neo4j-native vector store using built-in ANN indexes."""

    def __init__(
        self,
        driver: AsyncDriver | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._driver = driver
        self._owned_driver = driver is None
        self._embedding_model = None  # lazy-loaded

    # ------------------------------------------------------------------
    # Driver access
    # ------------------------------------------------------------------

    async def _get_driver(self) -> AsyncDriver:
        if self._driver is None:
            self._driver = await get_driver(self.settings)
        return self._driver

    async def close(self) -> None:
        if self._owned_driver and self._driver is not None:
            await self._driver.close()
            self._driver = None

    # ------------------------------------------------------------------
    # Embedding model (lazy-loaded)
    # ------------------------------------------------------------------

    def _get_embedding_model(self) -> object:
        """Get or initialize the embedding model.

        Production: Requires sentence_transformers installed. Fails hard if unavailable.
        """
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer

            model_name = getattr(self.settings, "embedding_model", "all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer(model_name)
            logger.info("Loaded embedding model: %s", model_name)
        return self._embedding_model

    def _embed(self, text: str) -> list[float]:
        model = self._get_embedding_model()
        return model.encode(text, normalize_embeddings=True).tolist()

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_embedding_model()
        return [
            v.tolist()
            for v in model.encode(texts, normalize_embeddings=True, batch_size=32)
        ]

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upsert a single entity embedding into Neo4j."""
        if entity_type not in VECTOR_ENTITY_TYPES:
            raise VectorStoreError(
                f"Unknown entity type '{entity_type}'. Supported: {VECTOR_ENTITY_TYPES}"
            )

        embedding = self._embed(text)
        driver = await self._get_driver()

        params: dict[str, Any] = {
            "id": entity_id,
            "embedding": embedding,
            "text": text[:2000],
            "metadata": {
                k: v
                for k, v in (metadata or {}).items()
                if isinstance(v, (str, int, float, bool))
            },
        }

        query = f"""
        MERGE (n:{entity_type} {{id: $id}})
        ON CREATE SET
            n.embedding = $embedding,
            n.embedding_text = $text,
            n += $metadata,
            n.embedding_updated_at = datetime()
        ON MATCH SET
            n.embedding = $embedding,
            n.embedding_text = $text,
            n.embedding_updated_at = datetime()
        RETURN n.id AS entity_id, true AS upserted
        """

        try:
            async with driver.session(database=self.settings.neo4j_database) as session:
                result = await session.run(query, params)
                record = await result.single()
                return {
                    "entity_id": record["entity_id"] if record else entity_id,
                    "entity_type": entity_type,
                    "upserted": record["upserted"] if record else False,
                }
        except (ClientError, ServiceUnavailable) as exc:
            raise VectorStoreError(
                f"Failed to upsert entity {entity_id}: {exc}"
            ) from exc

    async def upsert_batch(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> dict[str, Any]:
        """Batch upsert entity embeddings."""
        if not entities:
            return {"upserted": 0, "failed": []}

        texts = [e.get("text", e.get("name", "")) for e in entities]
        embeddings = self._embed_batch(texts)

        records = []
        for entity, embedding, text in zip(entities, embeddings, texts):
            records.append(
                {
                    "id": entity["id"],
                    "embedding": embedding,
                    "text": text[:2000],
                    "metadata": {
                        k: v
                        for k, v in entity.items()
                        if k not in ("id", "text", "embedding")
                        and isinstance(v, (str, int, float, bool))
                    },
                }
            )

        query = f"""
        UNWIND $records AS rec
        MERGE (n:{entity_type} {{id: rec.id}})
        ON CREATE SET
            n.embedding = rec.embedding,
            n.embedding_text = rec.text,
            n += rec.metadata,
            n.embedding_updated_at = datetime()
        ON MATCH SET
            n.embedding = rec.embedding,
            n.embedding_text = rec.text,
            n.embedding_updated_at = datetime()
        RETURN count(n) AS upserted
        """

        driver = await self._get_driver()
        try:
            async with driver.session(database=self.settings.neo4j_database) as session:
                result = await session.run(query, {"records": records})
                record = await result.single()
                return {"upserted": record["upserted"] if record else 0, "failed": []}
        except (ClientError, ServiceUnavailable) as exc:
            logger.error("Batch upsert failed for %s: %s", entity_type, exc)
            return {"upserted": 0, "failed": [e["id"] for e in entities]}

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def search(
        self,
        query_text: str,
        entity_type: str | None = None,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """ANN vector search using Neo4j native vector index."""
        query_embedding = self._embed(query_text)
        driver = await self._get_driver()
        types_to_search = [entity_type] if entity_type else VECTOR_ENTITY_TYPES
        all_results: list[tuple[str, float, dict[str, Any]]] = []

        for etype in types_to_search:
            index_name = f"{etype.lower()}_embedding_idx"
            cypher = """
            CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
            YIELD node, score
            WHERE score >= $min_score
            RETURN
                node.id AS entity_id,
                labels(node)[0] AS entity_type,
                score,
                node.name AS name,
                node.description AS description,
                node.confidence AS confidence
            ORDER BY score DESC
            """
            try:
                async with driver.session(
                    database=self.settings.neo4j_database
                ) as session:
                    result = await session.run(
                        cypher,
                        {
                            "index_name": index_name,
                            "top_k": top_k,
                            "embedding": query_embedding,
                            "min_score": min_score,
                        },
                    )
                    async for record in result:
                        all_results.append(
                            (
                                record["entity_id"],
                                record["score"],
                                {
                                    "entity_type": record["entity_type"],
                                    "name": record["name"],
                                    "description": record["description"],
                                    "confidence": record["confidence"],
                                },
                            )
                        )
            except ClientError as exc:
                if (
                    "index does not exist" in str(exc).lower()
                    or "no such index" in str(exc).lower()
                ):
                    logger.warning(
                        "Vector index '%s' not found — falling back for %s",
                        index_name,
                        etype,
                    )
                    continue
                logger.error("Vector search failed for %s: %s", etype, exc)

        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]

    async def delete_entity(self, entity_id: str, tenant_id: str) -> bool:
        """Remove the embedding property from an entity node with tenant filtering.
        
        Args:
            entity_id: Entity identifier
            tenant_id: Tenant identifier (required for multi-tenant security)
            
        Returns:
            True if embedding was deleted, False otherwise
            
        Raises:
            ValueError: If tenant_id is None or empty
        """
        if not tenant_id:
            raise ValueError("tenant_id is required for delete_entity")
        
        driver = await self._get_driver()
        query = """
        MATCH (n {id: $id, tenant_id: $tenant_id})
        REMOVE n.embedding, n.embedding_text, n.embedding_updated_at
        RETURN count(n) AS updated
        """
        try:
            async with driver.session(database=self.settings.neo4j_database) as session:
                result = await session.run(query, {"id": entity_id, "tenant_id": tenant_id})
                record = await result.single()
                return bool(record and record["updated"] > 0)
        except (ClientError, ServiceUnavailable) as exc:
            logger.error("Failed to delete embedding for %s: %s", entity_id, exc)
            return False

    async def index_health(self) -> dict[str, Any]:
        """Check whether all expected vector indexes exist and are online."""
        driver = await self._get_driver()
        details: dict[str, Any] = {}
        all_online = True

        try:
            async with driver.session(database=self.settings.neo4j_database) as session:
                result = await session.run(
                    "SHOW INDEXES YIELD name, type, state WHERE type = 'VECTOR'"
                )
                existing = {r["name"]: r["state"] async for r in result}

            for etype in VECTOR_ENTITY_TYPES:
                index_name = f"{etype.lower()}_embedding_idx"
                state = existing.get(index_name)
                online = state == "ONLINE"
                if not online:
                    all_online = False
                details[index_name] = {
                    "entity_type": etype,
                    "state": state or "MISSING",
                    "online": online,
                }

        except (ClientError, ServiceUnavailable) as exc:
            return {"status": "unhealthy", "error": str(exc), "indexes": {}}

        return {
            "status": "healthy" if all_online else "degraded",
            "indexes": details,
        }


# Backwards-compatibility alias
VectorStore = Neo4jVectorStore
