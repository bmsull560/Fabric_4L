"""Coreference resolution for identifying and merging duplicate entities.

Implements the CoreferenceResolver from spec (lines 535-686).
Handles cases like "inventory tracking" vs "automated stock management".
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

from layer2_extraction.models import (
    Capability,
    Feature,
    Persona,
    PredicateType,
    Relationship,
    UseCase,
    ValueDriver,
)


class ResolutionMethod(str, Enum):
    """Method used for coreference resolution."""

    EXACT_MATCH = "exact_match"
    NORMALIZED_MATCH = "normalized_match"
    ALTERNATIVE_NAME_OVERLAP = "alternative_name_overlap"
    SEMANTICALLY_EQUIVALENT = "semantically_equivalent"
    CAPABILITY_HIERARCHY = "capability_hierarchy"
    VECTOR_SIMILARITY = "vector_similarity"
    RULE_BASED = "rule_based"


@dataclass
class CoreferenceCluster:
    """Cluster of coreferent entities."""

    cluster_id: str
    canonical_entity_id: str
    canonical_name: str
    entity_type: type
    member_entity_ids: list[str]
    confidence: float
    resolution_method: ResolutionMethod


@dataclass
class CoreferenceRule:
    """Rule for identifying coreferences."""

    name: str
    entity_types: list[type]
    match_criteria: dict[str, Any]
    confidence_boost: float


class CoreferenceResolver:
    """
    Identifies and resolves coreferences between extracted entities.
    Handles cases like "inventory tracking" vs "automated stock management".
    """

    def __init__(self):
        """Initialize resolver with coreference resolution rules."""
        self.resolution_rules = self._initialize_rules()

    def _initialize_rules(self) -> list[CoreferenceRule]:
        """Initialize coreference resolution rules."""
        return [
            CoreferenceRule(
                name="exact_name_match",
                entity_types=[Capability, UseCase, Persona, ValueDriver, Feature],
                match_criteria={"name_similarity": "exact"},
                confidence_boost=1.0,
            ),
            CoreferenceRule(
                name="normalized_name_match",
                entity_types=[Capability, UseCase, Persona, ValueDriver, Feature],
                match_criteria={"name_similarity": "normalized"},
                confidence_boost=0.95,
            ),
            CoreferenceRule(
                name="shared_alternative_name",
                entity_types=[Capability, UseCase, Persona, ValueDriver, Feature],
                match_criteria={"alternative_name_overlap": True},
                confidence_boost=0.90,
            ),
            CoreferenceRule(
                name="capability_hierarchy",
                entity_types=[Capability],
                match_criteria={"parent_child_overlap": True},
                confidence_boost=0.85,
            ),
        ]

    def resolve_coreferences(
        self, entities: list[Any], relationships: list[Relationship]
    ) -> list[CoreferenceCluster]:
        """
        Identify coreference clusters among extracted entities.

        Args:
            entities: All extracted entities
            relationships: All extracted relationships

        Returns:
            List of coreference clusters
        """
        clusters = []
        processed_ids = set()

        # Group entities by type
        entities_by_type: dict[type, list[Any]] = {}
        for entity in entities:
            entity_type = type(entity)
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Build semantically equivalent pairs from relationships
        semantically_equivalent_pairs = self._get_semantically_equivalent_pairs(relationships)

        # Process each type group
        for entity_type, type_entities in entities_by_type.items():
            for i, entity1 in enumerate(type_entities):
                if entity1.id in processed_ids:
                    continue

                cluster_members = [entity1]

                for entity2 in type_entities[i + 1 :]:
                    if entity2.id in processed_ids:
                        continue

                    if self._check_coreference(entity1, entity2, semantically_equivalent_pairs):
                        cluster_members.append(entity2)

                if len(cluster_members) > 1:
                    cluster = self._create_cluster(cluster_members)
                    clusters.append(cluster)
                    for member in cluster_members:
                        processed_ids.add(member.id)

        return clusters

    def _get_semantically_equivalent_pairs(
        self, relationships: list[Relationship]
    ) -> set[tuple[str, str]]:
        """Extract semantically equivalent pairs from relationships."""
        pairs = set()
        for rel in relationships:
            if rel.canonical_predicate == PredicateType.SEMANTICALLY_EQUIVALENT:
                pair = tuple(sorted([rel.source_id, rel.target_id]))
                pairs.add(pair)
        return pairs

    def _check_coreference(
        self, entity1: Any, entity2: Any, semantically_equivalent_pairs: set[tuple[str, str]]
    ) -> bool:
        """Check if two entities are coreferent."""
        # Exact name match
        name1 = self._get_entity_name(entity1)
        name2 = self._get_entity_name(entity2)

        if name1.lower() == name2.lower():
            return True

        # Normalized name match
        norm1 = self._normalize_for_comparison(name1)
        norm2 = self._normalize_for_comparison(name2)
        if norm1 == norm2:
            return True

        # Alternative name overlap
        all_names1 = {name1.lower()}
        all_names2 = {name2.lower()}

        # Add alternative names if available
        if hasattr(entity1, "alternative_names"):
            all_names1.update(n.lower() for n in entity1.alternative_names)
        if hasattr(entity2, "alternative_names"):
            all_names2.update(n.lower() for n in entity2.alternative_names)

        if all_names1 & all_names2:
            return True

        # Semantic equivalence relationship
        pair = tuple(sorted([entity1.id, entity2.id]))
        if pair in semantically_equivalent_pairs:
            return True

        return False

    def _get_entity_name(self, entity: Any) -> str:
        """Get the canonical name of an entity."""
        if isinstance(entity, Capability) or isinstance(entity, UseCase):
            return entity.name
        elif isinstance(entity, Persona):
            return entity.title
        elif isinstance(entity, ValueDriver) or isinstance(entity, Feature):
            return entity.name
        return str(entity.id)

    def _normalize_for_comparison(self, name: str) -> str:
        """Normalize name for coreference comparison."""
        # Remove common suffixes/prefixes
        stop_words = {
            "system",
            "solution",
            "platform",
            "module",
            "feature",
            "capability",
            "functionality",
            "service",
            "tool",
        }
        words = name.lower().split()
        words = [w for w in words if w not in stop_words]
        return " ".join(sorted(words))

    def _create_cluster(self, members: list[Any]) -> CoreferenceCluster:
        """Create a coreference cluster from member entities."""
        # Select canonical entity (highest confidence or shortest name)
        canonical = max(
            members, key=lambda e: (getattr(e, "confidence", 0), -len(self._get_entity_name(e)))
        )

        return CoreferenceCluster(
            cluster_id=f"cluster-{uuid4().hex[:8]}",
            canonical_entity_id=canonical.id,
            canonical_name=self._get_entity_name(canonical),
            entity_type=type(canonical),
            member_entity_ids=[m.id for m in members],
            confidence=getattr(canonical, "confidence", 0),
            resolution_method=ResolutionMethod.RULE_BASED,
        )

    def apply_clusters_to_entities(
        self, entities: dict[str, list[Any]], clusters: list[CoreferenceCluster]
    ) -> dict[str, list[Any]]:
        """Apply coreference clusters to deduplicate entities.

        Args:
            entities: Dict of entity lists by type
            clusters: List of coreference clusters

        Returns:
            Deduplicated entity dict with updated IDs
        """
        # Build ID mapping from clusters
        id_mapping: dict[str, str] = {}
        for cluster in clusters:
            for member_id in cluster.member_entity_ids:
                if member_id != cluster.canonical_entity_id:
                    id_mapping[member_id] = cluster.canonical_entity_id

        # Apply mapping to all entities
        deduplicated = {}
        for entity_type, entity_list in entities.items():
            seen_ids = set()
            filtered = []
            for entity in entity_list:
                # Skip if this ID has been merged
                if entity.id in id_mapping:
                    continue
                # Skip if we've seen this canonical ID
                if entity.id in seen_ids:
                    continue
                seen_ids.add(entity.id)
                filtered.append(entity)
            deduplicated[entity_type] = filtered

        return deduplicated

    def apply_clusters_to_relationships(
        self, relationships: list[Relationship], clusters: list[CoreferenceCluster]
    ) -> list[Relationship]:
        """Update relationship references after coreference resolution.

        Args:
            relationships: List of relationships
            clusters: List of coreference clusters

        Returns:
            Updated relationships with remapped IDs
        """
        # Build ID mapping
        id_mapping: dict[str, str] = {}
        for cluster in clusters:
            for member_id in cluster.member_entity_ids:
                if member_id != cluster.canonical_entity_id:
                    id_mapping[member_id] = cluster.canonical_entity_id

        # Update relationship references
        for rel in relationships:
            if rel.source_id in id_mapping:
                rel.source_id = id_mapping[rel.source_id]
            if rel.target_id in id_mapping:
                rel.target_id = id_mapping[rel.target_id]

        return relationships
