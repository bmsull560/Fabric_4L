"""Semantic alignment for entity deduplication using vector similarity.

Aligns extracted entities against existing ontology using vector-based
similarity and fuzzy matching. Implements spec alignment logic (lines 356-508).
"""

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

# OpenAI import with graceful fallback
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from layer2_extraction.models import (
    Capability,
    ExtractionResult,
    Feature,
    Persona,
    UseCase,
    ValueDriver,
)


class AlignmentMethod(str, Enum):
    """Method used for alignment."""

    VECTOR_SIMILARITY = "vector_similarity"
    EXACT_MATCH = "exact_match"
    NORMALIZED_MATCH = "normalized_match"
    NO_CANDIDATES = "no_candidates"
    BELOW_THRESHOLD = "below_threshold"


@dataclass
class AlignmentCandidate:
    """Candidate for semantic alignment."""

    candidate_id: str
    canonical_form: str
    entity_type: type
    vector_embedding: list[float] | None = None
    source_ontology: str = "value_fabric"
    confidence: float = 0.0


@dataclass
class AlignmentResult:
    """Result of semantic alignment."""

    extracted_entity_id: str
    aligned_entity_id: str | None
    alignment_score: float
    alignment_method: AlignmentMethod
    is_new_entity: bool
    suggested_canonical_name: str | None = None


class SemanticAligner:
    """
    Aligns extracted entities against the formal ontology using
    vector-based similarity and fuzzy matching.

    Similarity threshold defaults to 0.85 as per spec.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        api_key: str | None = None,
        model: str = "text-embedding-3-large",
    ):
        """Initialize aligner.

        Args:
            similarity_threshold: Cosine similarity threshold for alignment (0.0-1.0)
            api_key: OpenAI API key for embeddings (required for align_* methods)
            model: Embedding model to use
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.similarity_threshold = similarity_threshold
        self.model = model
        self.alignment_cache: dict[str, AlignmentResult] = {}
        # API key is optional - only required for embedding-based alignment methods
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def align_result(
        self, result: ExtractionResult
    ) -> tuple[ExtractionResult, list[AlignmentResult]]:
        """Align all entities in an extraction result.

        Args:
            result: Extraction result with entities to align

        Returns:
            Tuple of (updated result, list of alignment results)
        """
        all_alignment_results = []

        # Align capabilities
        if result.capabilities:
            aligned_caps, alignments = await self.align_entities(result.capabilities)
            result.capabilities = aligned_caps
            all_alignment_results.extend(alignments)

        # Align use cases
        if result.use_cases:
            aligned_ucs, alignments = await self.align_entities(result.use_cases)
            result.use_cases = aligned_ucs
            all_alignment_results.extend(alignments)

        # Align personas
        if result.personas:
            aligned_personas, alignments = await self.align_entities(result.personas)
            result.personas = aligned_personas
            all_alignment_results.extend(alignments)

        # Align value drivers
        if result.value_drivers:
            aligned_vds, alignments = await self.align_entities(result.value_drivers)
            result.value_drivers = aligned_vds
            all_alignment_results.extend(alignments)

        # Align features
        if result.features:
            aligned_features, alignments = await self.align_entities(result.features)
            result.features = aligned_features
            all_alignment_results.extend(alignments)

        return result, all_alignment_results

    async def align_entities(self, entities: list[Any]) -> tuple[list[Any], list[AlignmentResult]]:
        """Align a list of entities.

        Args:
            entities: List of entities to align

        Returns:
            Tuple of (aligned entities, alignment results)
        """
        if not entities:
            return [], []

        # Get entity type
        type(entities[0])

        # Generate embeddings for all entities
        texts = [self._entity_to_text(e) for e in entities]
        embeddings = await self._get_embeddings(texts)

        # For each entity, check cache first, then align
        aligned_entities = []
        alignment_results = []

        # Pre-compute lookup structures for O(1) exact and normalized-name matching.
        # These are rebuilt incrementally as entities are added to aligned_entities.
        exact_name_index: dict[str, Any] = {}      # lower(name) -> entity
        normalized_name_index: dict[str, Any] = {} # normalized(name) -> entity
        # Parallel list of pre-normalized names matching aligned_entities order.
        aligned_normalized_names: list[str] = []

        for entity, embedding in zip(entities, embeddings):
            # Check cache
            cache_key = self._compute_cache_key(entity)
            if cache_key in self.alignment_cache:
                alignment_results.append(self.alignment_cache[cache_key])
                # Keep index structures in sync even for cached entities.
                entity_name = self._get_entity_name(entity)
                lower_name = entity_name.lower()
                normalized = self._normalize_name(entity_name)
                exact_name_index.setdefault(lower_name, entity)
                normalized_name_index.setdefault(normalized, entity)
                aligned_normalized_names.append(normalized)
                aligned_entities.append(entity)
                continue

            entity_name = self._get_entity_name(entity)
            lower_name = entity_name.lower()
            normalized_name = self._normalize_name(entity_name)

            # Check for exact/normalized matches within the same batch.
            # Exact and normalized lookups are O(1) via pre-built dicts.
            best_match = None
            best_score = 0.0
            best_method = AlignmentMethod.BELOW_THRESHOLD

            # 1. Exact name match (O(1))
            if lower_name in exact_name_index:
                best_match = exact_name_index[lower_name]
                best_score = 1.0
                best_method = AlignmentMethod.EXACT_MATCH

            # 2. Normalized name match (O(1)), only if no exact match yet
            if best_match is None and normalized_name in normalized_name_index:
                best_match = normalized_name_index[normalized_name]
                best_score = 0.95
                best_method = AlignmentMethod.NORMALIZED_MATCH

            # 3. Vector similarity – only needed when no name-based match found
            if best_match is None and embedding is not None:
                for other_entity, other_embedding, _other_norm in zip(
                    aligned_entities,
                    embeddings[: len(aligned_entities)],
                    aligned_normalized_names,
                ):
                    if other_embedding is None:
                        continue
                    similarity = self._compute_similarity(embedding, other_embedding)
                    if similarity > best_score:
                        best_score = similarity
                        best_match = other_entity
                        best_method = AlignmentMethod.VECTOR_SIMILARITY

            # Determine alignment result
            if best_match and best_score >= self.similarity_threshold:
                alignment_result = AlignmentResult(
                    extracted_entity_id=entity.id,
                    aligned_entity_id=best_match.id,
                    alignment_score=best_score,
                    alignment_method=best_method,
                    is_new_entity=False,
                    suggested_canonical_name=self._get_entity_name(best_match),
                )
                # Merge entity IDs (canonical wins)
                entity.id = best_match.id
            else:
                alignment_result = AlignmentResult(
                    extracted_entity_id=entity.id,
                    aligned_entity_id=None,
                    alignment_score=best_score,
                    alignment_method=AlignmentMethod.BELOW_THRESHOLD,
                    is_new_entity=True,
                    suggested_canonical_name=entity_name,
                )

            self.alignment_cache[cache_key] = alignment_result
            alignment_results.append(alignment_result)
            # Update O(1) lookup indexes before moving to the next entity.
            exact_name_index.setdefault(lower_name, entity)
            normalized_name_index.setdefault(normalized_name, entity)
            aligned_normalized_names.append(normalized_name)
            aligned_entities.append(entity)

        return aligned_entities, alignment_results

    def _entity_to_text(self, entity: Any) -> str:
        """Convert entity to text for embedding generation."""
        parts = []

        if isinstance(entity, Capability):
            parts.extend([entity.name, entity.description, "Features:", *entity.technical_features])
        elif isinstance(entity, UseCase):
            parts.extend([entity.name, entity.description, "Industries:", *entity.industry_context])
        elif isinstance(entity, Persona):
            parts.extend(
                [
                    entity.title,
                    f"Department: {entity.department}",
                    "Pain points:",
                    *entity.pain_points,
                ]
            )
        elif isinstance(entity, ValueDriver):
            parts.extend(
                [
                    entity.name,
                    entity.description,
                    f"Category: {entity.category.value}",
                    "Metrics:",
                    *entity.metrics,
                ]
            )
        elif isinstance(entity, Feature):
            parts.extend(
                [
                    entity.name,
                    entity.description,
                    f"Status: {entity.implementation_status}",
                    "Technical spec:",
                    entity.technical_spec or "",
                ]
            )

        return "\n".join(filter(None, parts))

    def _get_entity_name(self, entity: Any) -> str:
        """Get the canonical name of an entity."""
        if isinstance(entity, Capability) or isinstance(entity, UseCase):
            return entity.name
        elif isinstance(entity, Persona):
            return entity.title
        elif isinstance(entity, ValueDriver) or isinstance(entity, Feature):
            return entity.name
        return str(entity.id)

    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison."""
        # Remove common suffixes/prefixes and normalize whitespace
        stop_words = {"system", "solution", "platform", "module", "feature", "capability"}
        words = name.lower().strip().replace("-", " ").replace("_", " ").split()
        words = [w for w in words if w not in stop_words]
        return " ".join(sorted(words))

    def _compute_cache_key(self, entity: Any) -> str:
        """Compute cache key for alignment result."""
        entity_type = type(entity).__name__
        entity_name = self._get_entity_name(entity)
        key_data = f"{entity_type}:{entity_name}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def _get_embeddings(self, texts: list[str]) -> list[list[float] | None]:
        """Generate embeddings for texts using OpenAI API."""
        if not texts:
            return []

        if self.client is None:
            raise RuntimeError(
                "OpenAI API key required for embeddings. Pass api_key to SemanticAligner."
            )

        # Batch in chunks of 100 (OpenAI limit)
        all_embeddings: list[list[float] | None] = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = await self.client.embeddings.create(model=self.model, input=batch)
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception:
                # Return None for failed batch only
                all_embeddings.extend([None] * len(batch))

        return all_embeddings

    def _compute_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Compute cosine similarity between embeddings."""
        if embedding1 is None or embedding2 is None:
            return 0.0

        # Convert to numpy arrays
        v1 = np.array(embedding1)
        v2 = np.array(embedding2)

        # Compute cosine similarity
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(v1, v2) / (norm1 * norm2))
