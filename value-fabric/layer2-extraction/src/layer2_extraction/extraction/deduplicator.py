"""Semantic deduplication using embeddings.

Stage 4 of the extraction pipeline: Merges duplicate entities based on
embedding similarity with confidence threshold of 0.85.
"""

from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import numpy as np

# OpenAI import with graceful fallback
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from pydantic import BaseModel

from layer2_extraction.models import (
    Capability, UseCase, Persona, ValueDriver, Feature,
    Relationship
)
from layer2_extraction.coreference import CoreferenceResolver, CoreferenceCluster


class DeduplicationError(Exception):
    """Raised when deduplication fails."""
    pass


class EntityDeduplicator:
    """Deduplicate entities using semantic embeddings.
    
    Uses text-embedding-3-large to generate embeddings and merges
    entities with cosine similarity > threshold (default 0.85).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        similarity_threshold: float = 0.85
    ):
        """Initialize deduplicator.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model to use
            similarity_threshold: Cosine similarity threshold for merging (0.0-1.0)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.threshold = similarity_threshold
    
    async def deduplicate(
        self,
        entities: Dict[str, List[BaseModel]],
        relationships: Optional[List[Relationship]] = None,
        enable_coreference: bool = True
    ) -> Dict[str, List[BaseModel]]:
        """Deduplicate entities by type.
        
        Args:
            entities: Dict with keys: capabilities, use_cases, personas, value_drivers, features
            relationships: Optional list of relationships for coreference resolution
            enable_coreference: Whether to run coreference resolution before embedding dedup
            
        Returns:
            Dict with deduplicated entities and merged IDs tracked
        """
        # Stage 1: Coreference Resolution (if enabled and relationships provided)
        if enable_coreference and relationships:
            resolver = CoreferenceResolver()
            
            # Flatten all entities for coreference detection
            all_entities_flat = []
            for entity_list in entities.values():
                all_entities_flat.extend(entity_list)
            
            # Resolve coreferences
            clusters = resolver.resolve_coreferences(all_entities_flat, relationships)
            
            # Apply clusters to entities
            entities = resolver.apply_clusters_to_entities(entities, clusters)
        
        # Stage 2: Embedding-based deduplication
        results = {}
        
        # Deduplicate each entity type separately
        for entity_type, entity_list in entities.items():
            if entity_list:
                deduped = await self._deduplicate_type(entity_type, entity_list)
                results[entity_type] = deduped
            else:
                results[entity_type] = []
        
        return results
    
    async def _deduplicate_type(
        self,
        entity_type: str,
        entities: List[BaseModel]
    ) -> List[BaseModel]:
        """Deduplicate a single entity type.
        
        Strategy:
        1. Generate embeddings for all entities
        2. Compute pairwise similarity matrix
        3. Cluster entities above threshold
        4. Merge clusters, keeping canonical entity (most source refs)
        """
        if len(entities) <= 1:
            return entities
        
        # Generate embeddings
        texts = [self._entity_to_text(e) for e in entities]
        embeddings = await self._get_embeddings(texts)
        
        # Compute similarity matrix
        similarity_matrix = self._compute_similarity_matrix(embeddings)
        
        # Find merge clusters using greedy approach
        clusters = self._find_clusters(similarity_matrix)
        
        # Merge clusters
        deduplicated = []
        merged_ids = {}  # Maps old IDs to canonical IDs
        
        for cluster in clusters:
            if len(cluster) == 1:
                # Single entity, no merging needed
                deduplicated.append(entities[cluster[0]])
            else:
                # Merge cluster - select canonical and merge others into it
                cluster_entities = [entities[i] for i in cluster]
                canonical = self._select_canonical(cluster_entities)
                
                # Track merged IDs
                for entity in cluster_entities:
                    if entity.id != canonical.id:
                        merged_ids[entity.id] = canonical.id
                
                # Merge data into canonical
                self._merge_into_canonical(canonical, cluster_entities)
                deduplicated.append(canonical)
        
        return deduplicated
    
    def _entity_to_text(self, entity: BaseModel) -> str:
        """Convert entity to text for embedding generation.
        
        Includes key fields that define semantic meaning.
        """
        parts = []
        
        if isinstance(entity, Capability):
            parts.extend([
                entity.name,
                entity.description,
                "Features:",
                *entity.technical_features
            ])
        elif isinstance(entity, UseCase):
            parts.extend([
                entity.name,
                entity.description,
                "Industries:",
                *entity.industry_context
            ])
        elif isinstance(entity, Persona):
            parts.extend([
                entity.title,
                f"Department: {entity.department}",
                "Pain points:",
                *entity.pain_points
            ])
        elif isinstance(entity, ValueDriver):
            parts.extend([
                entity.name,
                entity.description,
                f"Category: {entity.category.value}",
                "Metrics:",
                *entity.metrics
            ])
        elif isinstance(entity, Feature):
            parts.extend([
                entity.name,
                entity.description,
                f"Status: {entity.implementation_status}",
                "Technical spec:",
                entity.technical_spec or ""
            ])
        
        return "\n".join(filter(None, parts))
    
    async def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts using OpenAI API."""
        try:
            # Batch in chunks of 100 (OpenAI limit)
            all_embeddings = []
            batch_size = 100
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return np.array(all_embeddings)
            
        except Exception as e:
            raise DeduplicationError(f"Failed to generate embeddings: {e}")
    
    def _compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute cosine similarity matrix for embeddings."""
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms
        
        # Compute similarity matrix
        similarity = np.dot(normalized, normalized.T)
        
        return similarity
    
    def _find_clusters(self, similarity_matrix: np.ndarray) -> List[List[int]]:
        """Find clusters of similar entities using greedy approach.
        
        Returns list of clusters, where each cluster is a list of indices.
        """
        n = len(similarity_matrix)
        unclustered = set(range(n))
        clusters = []
        
        while unclustered:
            # Start new cluster with first unclustered item
            seed = min(unclustered)
            cluster = [seed]
            unclustered.remove(seed)
            
            # Find all items similar to any item in cluster
            to_check = [seed]
            while to_check:
                current = to_check.pop(0)
                
                # Find all unclustered items similar to current
                for i in list(unclustered):
                    if similarity_matrix[current][i] >= self.threshold:
                        cluster.append(i)
                        unclustered.remove(i)
                        to_check.append(i)
            
            clusters.append(cluster)
        
        return clusters
    
    def _select_canonical(self, entities: List[BaseModel]) -> BaseModel:
        """Select canonical entity from cluster.
        
        Selects entity with most source references as canonical.
        Ties broken by highest confidence.
        """
        def score(entity):
            source_count = len(getattr(entity, "source_refs", []))
            confidence = getattr(entity, "confidence", 0)
            return (source_count, confidence)
        
        return max(entities, key=score)
    
    def _merge_into_canonical(
        self,
        canonical: BaseModel,
        entities: List[BaseModel]
    ) -> None:
        """Merge data from all entities into canonical.
        
        Preserves canonical ID, merges source references and other fields.
        """
        # Merge source references
        all_refs = set(canonical.source_refs if hasattr(canonical, "source_refs") else [])
        for entity in entities:
            if hasattr(entity, "source_refs"):
                all_refs.update(entity.source_refs)
        
        if hasattr(canonical, "source_refs"):
            canonical.source_refs = list(all_refs)
        
        # Keep highest confidence
        confidences = [
            getattr(e, "confidence", 0)
            for e in entities
        ]
        canonical.confidence = max(confidences)
        
        # For lists, merge unique items
        if isinstance(canonical, Capability):
            self._merge_capability_fields(canonical, entities)
        elif isinstance(canonical, UseCase):
            self._merge_usecase_fields(canonical, entities)
        elif isinstance(canonical, Persona):
            self._merge_persona_fields(canonical, entities)
        elif isinstance(canonical, ValueDriver):
            self._merge_valuedriver_fields(canonical, entities)
        elif isinstance(canonical, Feature):
            self._merge_feature_fields(canonical, entities)
    
    def _merge_capability_fields(
        self,
        canonical: Capability,
        entities: List[BaseModel]
    ) -> None:
        """Merge capability-specific fields."""
        all_features = set(canonical.technical_features)
        all_apis = set(canonical.api_endpoints)
        all_integrations = set(canonical.integrations)
        
        for entity in entities:
            if isinstance(entity, Capability):
                all_features.update(entity.technical_features)
                all_apis.update(entity.api_endpoints)
                all_integrations.update(entity.integrations)
        
        canonical.technical_features = list(all_features)
        canonical.api_endpoints = list(all_apis)
        canonical.integrations = list(all_integrations)
    
    def _merge_usecase_fields(
        self,
        canonical: UseCase,
        entities: List[BaseModel]
    ) -> None:
        """Merge use case-specific fields."""
        all_industries = set(canonical.industry_context)
        all_steps = canonical.workflow_steps[:]  # Preserve order
        all_kpis = set(canonical.kpis)
        
        for entity in entities:
            if isinstance(entity, UseCase):
                all_industries.update(entity.industry_context)
                all_kpis.update(entity.kpis)
                # Add unique steps preserving order
                for step in entity.workflow_steps:
                    if step not in all_steps:
                        all_steps.append(step)
        
        canonical.industry_context = list(all_industries)
        canonical.workflow_steps = all_steps
        canonical.kpis = list(all_kpis)
    
    def _merge_persona_fields(
        self,
        canonical: Persona,
        entities: List[BaseModel]
    ) -> None:
        """Merge persona-specific fields."""
        all_pain_points = set(canonical.pain_points)
        all_metrics = set(canonical.success_metrics)
        all_influencers = set(canonical.influenced_by)
        
        for entity in entities:
            if isinstance(entity, Persona):
                all_pain_points.update(entity.pain_points)
                all_metrics.update(entity.success_metrics)
                all_influencers.update(entity.influenced_by)
        
        canonical.pain_points = list(all_pain_points)
        canonical.success_metrics = list(all_metrics)
        canonical.influenced_by = list(all_influencers)
    
    def _merge_valuedriver_fields(
        self,
        canonical: ValueDriver,
        entities: List[BaseModel]
    ) -> None:
        """Merge value driver-specific fields."""
        all_metrics = set(canonical.metrics)
        
        for entity in entities:
            if isinstance(entity, ValueDriver):
                all_metrics.update(entity.metrics)
        
        canonical.metrics = list(all_metrics)
    
    def _merge_feature_fields(
        self,
        canonical: Feature,
        entities: List[BaseModel]
    ) -> None:
        """Merge feature-specific fields."""
        # Keep the most specific technical spec
        for entity in entities:
            if isinstance(entity, Feature):
                if entity.technical_spec and len(entity.technical_spec) > len(canonical.technical_spec or ""):
                    canonical.technical_spec = entity.technical_spec
        
        # Use most advanced status (ga > beta > planned > deprecated)
        status_priority = {"ga": 4, "beta": 3, "planned": 2, "deprecated": 1}
        best_status = canonical.implementation_status
        best_priority = status_priority.get(best_status, 0)
        
        for entity in entities:
            if isinstance(entity, Feature):
                entity_priority = status_priority.get(entity.implementation_status, 0)
                if entity_priority > best_priority:
                    best_status = entity.implementation_status
                    best_priority = entity_priority
        
        canonical.implementation_status = best_status


async def deduplicate_entities(
    entities: Dict[str, List[BaseModel]],
    api_key: Optional[str] = None,
    similarity_threshold: float = 0.85,
    relationships: Optional[List[Relationship]] = None,
    enable_coreference: bool = True
) -> Dict[str, List[BaseModel]]:
    """Convenience function to deduplicate entities.
    
    Args:
        entities: Dict of entity lists
        api_key: OpenAI API key
        similarity_threshold: Cosine similarity threshold
        relationships: Optional list of relationships for coreference resolution
        enable_coreference: Whether to run coreference resolution
        
    Returns:
        Deduplicated entity dict
    """
    deduplicator = EntityDeduplicator(
        api_key=api_key,
        similarity_threshold=similarity_threshold
    )
    return await deduplicator.deduplicate(
        entities,
        relationships=relationships,
        enable_coreference=enable_coreference
    )
