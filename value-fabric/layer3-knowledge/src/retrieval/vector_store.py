"""Vector store integration using Pinecone for entity embeddings."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Raised when vector store operation fails."""
    pass


class VectorStore:
    """Pinecone vector store for entity embeddings.

    Provides:
    - Entity embedding storage and retrieval
    - Similarity search with metadata filtering
    - Batch operations for efficiency
    - Hybrid search with sparse vectors (BM25)
    """

    def __init__(
        self,
        pinecone_client: Optional[Pinecone] = None,
        embedding_model: Optional[SentenceTransformer] = None,
        settings: Optional[Settings] = None,
    ):
        """Initialize vector store.

        Args:
            pinecone_client: Pinecone client instance
            embedding_model: SentenceTransformer model
            settings: Application settings
        """
        self.settings = settings or get_settings()

        # Initialize Pinecone client
        if pinecone_client:
            self.client = pinecone_client
        elif self.settings.pinecone_api_key:
            self.client = Pinecone(api_key=self.settings.pinecone_api_key)
        else:
            raise VectorStoreError("Pinecone API key not provided")

        # Initialize embedding model
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            self.embedding_model = SentenceTransformer(self.settings.embedding_model)

        # Ensure index exists
        self.index = self._get_or_create_index()
        self.namespace = self.settings.pinecone_namespace

    def _get_or_create_index(self) -> Any:
        """Get or create Pinecone index."""
        index_name = self.settings.pinecone_index

        # Check if index exists
        existing_indexes = self.client.list_indexes().names()

        if index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {index_name}")
            self.client.create_index(
                name=index_name,
                dimension=self.settings.pinecone_dimension,
                metric=self.settings.pinecone_metric,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        return self.client.Index(index_name)

    async def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Upsert a single entity embedding.

        Args:
            entity_id: Unique entity identifier
            entity_type: Type of entity (Capability, UseCase, etc.)
            text: Text to embed (name + description)
            metadata: Additional metadata to store

        Returns:
            Upsert response
        """
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()

        # Prepare metadata
        vector_metadata = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "text": text[:1000],  # Truncate for Pinecone metadata limits
        }
        if metadata:
            # Filter out complex types for Pinecone
            vector_metadata.update(self._clean_metadata(metadata))

        # Upsert to Pinecone
        response = self.index.upsert(
            vectors=[
                {
                    "id": entity_id,
                    "values": embedding,
                    "metadata": vector_metadata,
                }
            ],
            namespace=self.namespace,
        )

        logger.debug(f"Upserted entity {entity_id} ({entity_type})")
        return {"upserted_count": response.upserted_count}

    async def upsert_entities_batch(
        self,
        entities: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> dict:
        """Upsert multiple entities in batches.

        Args:
            entities: List of entity dictionaries with id, type, text, metadata
            batch_size: Number of entities per batch

        Returns:
            Batch upsert statistics
        """
        total_upserted = 0

        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]

            # Generate embeddings in batch
            texts = [e["text"] for e in batch]
            embeddings = self.embedding_model.encode(texts).tolist()

            # Prepare vectors
            vectors = []
            for entity, embedding in zip(batch, embeddings):
                vector_metadata = {
                    "entity_id": entity["id"],
                    "entity_type": entity["type"],
                    "text": entity["text"][:1000],
                }
                if "metadata" in entity:
                    vector_metadata.update(self._clean_metadata(entity["metadata"]))

                vectors.append(
                    {
                        "id": entity["id"],
                        "values": embedding,
                        "metadata": vector_metadata,
                    }
                )

            # Upsert batch
            response = self.index.upsert(
                vectors=vectors,
                namespace=self.namespace,
            )
            total_upserted += response.upserted_count

        logger.info(f"Batch upserted {total_upserted} entities")
        return {"upserted_count": total_upserted}

    async def search(
        self,
        query: str,
        entity_type: Optional[str] = None,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar entities.

        Args:
            query: Search query text
            entity_type: Filter by entity type
            top_k: Number of results to return
            filter_dict: Additional metadata filters

        Returns:
            List of matching entities with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Build filter
        search_filter = {}
        if entity_type:
            search_filter["entity_type"] = {"$eq": entity_type}
        if filter_dict:
            for key, value in filter_dict.items():
                search_filter[key] = {"$eq": value}

        # Search
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=search_filter if search_filter else None,
            namespace=self.namespace,
        )

        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append(
                {
                    "id": match.id,
                    "score": match.score,
                    "entity_type": match.metadata.get("entity_type"),
                    "text": match.metadata.get("text"),
                    "metadata": match.metadata,
                }
            )

        return formatted_results

    async def search_by_entity_id(
        self,
        entity_id: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find similar entities to a given entity ID.

        Args:
            entity_id: Entity ID to find similar entities for
            top_k: Number of similar entities to return

        Returns:
            List of similar entities
        """
        # Fetch the entity vector
        fetch_result = self.index.fetch(ids=[entity_id], namespace=self.namespace)

        if entity_id not in fetch_result.vectors:
            raise VectorStoreError(f"Entity {entity_id} not found in vector store")

        vector = fetch_result.vectors[entity_id]

        # Search for similar vectors
        results = self.index.query(
            vector=vector.values,
            top_k=top_k + 1,  # +1 to exclude the query entity itself
            include_metadata=True,
            namespace=self.namespace,
        )

        # Format results, excluding the query entity
        formatted_results = []
        for match in results.matches:
            if match.id != entity_id:
                formatted_results.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "entity_type": match.metadata.get("entity_type"),
                        "text": match.metadata.get("text"),
                        "metadata": match.metadata,
                    }
                )

        return formatted_results[:top_k]

    async def delete_entity(self, entity_id: str) -> dict:
        """Delete an entity from the vector store.

        Args:
            entity_id: Entity ID to delete

        Returns:
            Deletion status
        """
        self.index.delete(ids=[entity_id], namespace=self.namespace)
        logger.debug(f"Deleted entity {entity_id} from vector store")
        return {"deleted": True, "entity_id": entity_id}

    async def delete_entities_batch(self, entity_ids: List[str]) -> dict:
        """Delete multiple entities from the vector store.

        Args:
            entity_ids: List of entity IDs to delete

        Returns:
            Deletion status
        """
        self.index.delete(ids=entity_ids, namespace=self.namespace)
        logger.debug(f"Deleted {len(entity_ids)} entities from vector store")
        return {"deleted_count": len(entity_ids)}

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata for Pinecone storage.

        Pinecone only supports string, number, boolean, and list of strings.

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Cleaned metadata dictionary
        """
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, list) and all(isinstance(x, str) for x in value):
                cleaned[key] = value
            elif isinstance(value, list):
                # Convert non-string lists to comma-separated strings
                cleaned[key] = ", ".join(str(x) for x in value)
            else:
                # Convert other types to string
                cleaned[key] = str(value)
        return cleaned

    async def get_stats(self) -> dict:
        """Get vector store statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.index.describe_index_stats()
        return {
            "total_vector_count": stats.total_vector_count,
            "dimension": stats.dimension,
            "index_fullness": stats.index_fullness,
            "namespaces": list(stats.namespaces.keys()) if stats.namespaces else [],
        }
