"""Entailment validation for extracted entities and relationships.

Implements the 6 validation rules from the spec:
- VAL-001: Required properties must be present
- VAL-002: Domain/range constraints for relationships
- VAL-003: Relationship cardinality validation
- VAL-004: Hierarchy acyclicity check
- VAL-005: Consistency (no contradictory relationships)
- VAL-006: Confidence score bounds validation
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from ..models import (
    Capability, UseCase, Persona, ValueDriver, Feature,
    Relationship, PredicateType, ExtractionResult
)


class ValidationSeverity(str, Enum):
    """Severity level for validation results."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationRule:
    """Rule for validating extracted knowledge."""
    rule_id: str
    rule_type: str
    description: str
    severity: ValidationSeverity
    validation_function: str  # Name of validation function


@dataclass
class ValidationResult:
    """Result of validation check."""
    rule_id: str
    passed: bool
    severity: ValidationSeverity
    message: str
    affected_entities: List[str] = field(default_factory=list)
    affected_relationships: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None


# Domain/range constraints for relationships (from spec)
DOMAIN_RANGE_CONSTRAINTS: Dict[PredicateType, Tuple[List[type], List[type]]] = {
    PredicateType.ENABLES: ([Capability], [UseCase]),
    PredicateType.REQUIRES: ([UseCase], [Capability]),
    PredicateType.BENEFITS: ([UseCase], [Persona]),
    PredicateType.DRIVES: ([Persona], [ValueDriver]),
    PredicateType.CONTRIBUTES_TO: ([Capability], [ValueDriver]),
    PredicateType.DEPENDS_ON: ([Capability], [Capability]),
    PredicateType.ALTERNATIVE_TO: ([Capability], [Capability]),
    PredicateType.CAPABILITY_SUBTYPE_OF: ([Capability], [Capability]),
    PredicateType.CAPABILITY_REQUIRES_CAPABILITY: ([Capability], [Capability]),
    PredicateType.SEMANTICALLY_EQUIVALENT: (
        [Capability, UseCase, Persona, ValueDriver, Feature],
        [Capability, UseCase, Persona, ValueDriver, Feature]
    ),
    PredicateType.IMPLEMENTS: ([Feature], [Capability]),
    PredicateType.DELIVERS: ([UseCase], [ValueDriver]),
    PredicateType.INVOLVES: ([UseCase], [Persona]),
}


# Cardinality constraints (from spec)
CARDINALITY_CONSTRAINTS: Dict[PredicateType, Tuple[Optional[int], Optional[int]]] = {
    # (min, max) - None means unlimited
    PredicateType.ENABLES: (0, None),
    PredicateType.REQUIRES: (1, None),  # Use case should require at least 1 capability
    PredicateType.BENEFITS: (0, None),
    PredicateType.DRIVES: (0, None),
    PredicateType.CONTRIBUTES_TO: (0, None),
    PredicateType.DEPENDS_ON: (0, None),
    PredicateType.ALTERNATIVE_TO: (0, 1),  # Max 1 alternative
    PredicateType.CAPABILITY_SUBTYPE_OF: (0, 1),  # Max 1 parent in hierarchy
    PredicateType.CAPABILITY_REQUIRES_CAPABILITY: (0, None),
    PredicateType.SEMANTICALLY_EQUIVALENT: (0, None),
    PredicateType.IMPLEMENTS: (0, None),
    PredicateType.DELIVERS: (0, None),
    PredicateType.INVOLVES: (1, None),  # Use case should involve at least 1 persona
}


# Contradictory relationship pairs
CONTRADICTORY_PAIRS: List[Set[PredicateType]] = [
    {PredicateType.CAPABILITY_SUBTYPE_OF, PredicateType.CAPABILITY_REQUIRES_CAPABILITY},
    {PredicateType.ENABLES, PredicateType.DEPENDS_ON},  # Can be contradictory in some contexts
]


class EntailmentValidator:
    """Validates extracted entities and relationships against ontology constraints."""
    
    def __init__(self):
        """Initialize validator with validation rules."""
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize validation rule set."""
        return [
            ValidationRule(
                rule_id="VAL-001",
                rule_type="cardinality",
                description="Required properties must be present",
                severity=ValidationSeverity.ERROR,
                validation_function="validate_required_properties"
            ),
            ValidationRule(
                rule_id="VAL-002",
                rule_type="domain_range",
                description="Relationships must respect domain/range constraints",
                severity=ValidationSeverity.ERROR,
                validation_function="validate_domain_range"
            ),
            ValidationRule(
                rule_id="VAL-003",
                rule_type="cardinality",
                description="Relationship cardinality must be respected",
                severity=ValidationSeverity.WARNING,
                validation_function="validate_relationship_cardinality"
            ),
            ValidationRule(
                rule_id="VAL-004",
                rule_type="hierarchy",
                description="Inheritance hierarchies must be acyclic",
                severity=ValidationSeverity.ERROR,
                validation_function="validate_hierarchy_acyclic"
            ),
            ValidationRule(
                rule_id="VAL-005",
                rule_type="consistency",
                description="No contradictory relationships",
                severity=ValidationSeverity.ERROR,
                validation_function="validate_consistency"
            ),
            ValidationRule(
                rule_id="VAL-006",
                rule_type="confidence",
                description="Confidence scores should be reasonable",
                severity=ValidationSeverity.WARNING,
                validation_function="validate_confidence_scores"
            ),
        ]
    
    def validate(
        self,
        result: ExtractionResult,
        relationships: List[Relationship]
    ) -> List[ValidationResult]:
        """Validate extraction result against all rules.
        
        Args:
            result: Extraction result with entities
            relationships: List of relationships
            
        Returns:
            List of validation results
        """
        results = []
        
        # Validate required properties
        results.extend(self._validate_required_properties(result))
        
        # Validate domain/range constraints
        results.extend(self._validate_domain_range(result, relationships))
        
        # Validate relationship cardinality
        results.extend(self._validate_relationship_cardinality(result, relationships))
        
        # Validate hierarchy acyclicity
        results.extend(self._validate_hierarchy_acyclic(result, relationships))
        
        # Validate consistency
        results.extend(self._validate_consistency(result, relationships))
        
        # Validate confidence scores
        results.extend(self._validate_confidence_scores(result, relationships))
        
        return results
    
    def _get_entity_type(self, entity: Any) -> type:
        """Get the type of an entity."""
        if isinstance(entity, Capability):
            return Capability
        elif isinstance(entity, UseCase):
            return UseCase
        elif isinstance(entity, Persona):
            return Persona
        elif isinstance(entity, ValueDriver):
            return ValueDriver
        elif isinstance(entity, Feature):
            return Feature
        return type(entity)
    
    def _get_entity_by_id(self, entity_id: str, result: ExtractionResult) -> Optional[Any]:
        """Find entity by ID across all types."""
        return result.get_entity_by_id(entity_id)
    
    def _validate_required_properties(
        self,
        result: ExtractionResult
    ) -> List[ValidationResult]:
        """Validate that all required properties are present (VAL-001)."""
        results = []
        
        for entity in result.get_all_entities():
            # Check required fields based on entity type
            if isinstance(entity, Capability):
                if not entity.name or len(entity.name) < 1:
                    results.append(ValidationResult(
                        rule_id="VAL-001",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required property 'name' missing or empty for Capability",
                        affected_entities=[entity.id],
                        suggestion="Ensure all capabilities have a non-empty name"
                    ))
                if not entity.description or len(entity.description) < 10:
                    results.append(ValidationResult(
                        rule_id="VAL-001",
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Required property 'description' too short for Capability '{entity.name}'",
                        affected_entities=[entity.id],
                        suggestion="Provide a detailed description (minimum 10 characters)"
                    ))
            
            elif isinstance(entity, ValueDriver):
                if not entity.unit:
                    results.append(ValidationResult(
                        rule_id="VAL-001",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required property 'unit' missing for ValueDriver '{entity.name}'",
                        affected_entities=[entity.id],
                        suggestion="Specify the unit of measurement (USD, percentage, hours, etc.)"
                    ))
            
            elif isinstance(entity, Feature):
                if not entity.name or len(entity.name) < 1:
                    results.append(ValidationResult(
                        rule_id="VAL-001",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Required property 'name' missing or empty for Feature",
                        affected_entities=[entity.id],
                        suggestion="Ensure all features have a non-empty name"
                    ))
        
        return results
    
    def _validate_domain_range(
        self,
        result: ExtractionResult,
        relationships: List[Relationship]
    ) -> List[ValidationResult]:
        """Validate domain/range constraints for relationships (VAL-002)."""
        results = []
        
        for rel in relationships:
            constraint = DOMAIN_RANGE_CONSTRAINTS.get(rel.predicate)
            if not constraint:
                continue
            
            expected_domain, expected_range = constraint
            
            # Get source and target entities
            source = self._get_entity_by_id(rel.source_id, result)
            target = self._get_entity_by_id(rel.target_id, result)
            
            if source:
                source_type = self._get_entity_type(source)
                if source_type not in expected_domain:
                    results.append(ValidationResult(
                        rule_id="VAL-002",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Entity type {source_type.__name__} not in domain of {rel.predicate.value}",
                        affected_entities=[rel.source_id],
                        affected_relationships=[rel.id],
                        suggestion=f"Source must be one of: {[t.__name__ for t in expected_domain]}"
                    ))
            
            if target:
                target_type = self._get_entity_type(target)
                if target_type not in expected_range:
                    results.append(ValidationResult(
                        rule_id="VAL-002",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Entity type {target_type.__name__} not in range of {rel.predicate.value}",
                        affected_entities=[rel.target_id],
                        affected_relationships=[rel.id],
                        suggestion=f"Target must be one of: {[t.__name__ for t in expected_range]}"
                    ))
        
        return results
    
    def _validate_relationship_cardinality(
        self,
        result: ExtractionResult,
        relationships: List[Relationship]
    ) -> List[ValidationResult]:
        """Validate relationship cardinality constraints (VAL-003)."""
        results = []
        
        # Count relationships per entity by type
        rel_count: Dict[str, Dict[PredicateType, int]] = {}
        for rel in relationships:
            if rel.source_id not in rel_count:
                rel_count[rel.source_id] = {}
            if rel.predicate not in rel_count[rel.source_id]:
                rel_count[rel.source_id][rel.predicate] = 0
            rel_count[rel.source_id][rel.predicate] += 1
        
        # Check against constraints
        for entity_id, type_counts in rel_count.items():
            for predicate, count in type_counts.items():
                constraint = CARDINALITY_CONSTRAINTS.get(predicate)
                if not constraint:
                    continue
                
                min_card, max_card = constraint
                
                # Check minimum cardinality
                if min_card is not None and count < min_card:
                    results.append(ValidationResult(
                        rule_id="VAL-003",
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Entity {entity_id[:8]}... has {count} {predicate.value} relationships, below min of {min_card}",
                        affected_entities=[entity_id],
                        suggestion=f"Add more {predicate.value} relationships to meet minimum cardinality"
                    ))
                
                # Check maximum cardinality
                if max_card is not None and count > max_card:
                    results.append(ValidationResult(
                        rule_id="VAL-003",
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Entity {entity_id[:8]}... has {count} {predicate.value} relationships, exceeding max of {max_card}",
                        affected_entities=[entity_id],
                        suggestion="Review and consolidate redundant relationships"
                    ))
        
        return results
    
    def _validate_hierarchy_acyclic(
        self,
        result: ExtractionResult,
        relationships: List[Relationship]
    ) -> List[ValidationResult]:
        """Validate that inheritance hierarchies contain no cycles (VAL-004)."""
        results = []
        
        # Build hierarchy graph for subtype relationships
        hierarchy_edges: Dict[str, str] = {}
        for rel in relationships:
            if rel.predicate == PredicateType.CAPABILITY_SUBTYPE_OF:
                hierarchy_edges[rel.source_id] = rel.target_id
        
        # Check for cycles using DFS
        def has_cycle(node: str, visited: Set[str], path: Set[str]) -> bool:
            if node in path:
                return True
            if node in visited:
                return False
            visited.add(node)
            path.add(node)
            if node in hierarchy_edges:
                if has_cycle(hierarchy_edges[node], visited, path):
                    return True
            path.remove(node)
            return False
        
        visited: Set[str] = set()
        for node in hierarchy_edges:
            if has_cycle(node, visited, set()):
                results.append(ValidationResult(
                    rule_id="VAL-004",
                    passed=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Cycle detected in capability hierarchy starting from {node[:8]}...",
                    affected_entities=[node],
                    suggestion="Remove cyclic relationship to restore hierarchy"
                ))
        
        return results
    
    def _validate_consistency(
        self,
        result: ExtractionResult,
        relationships: List[Relationship]
    ) -> List[ValidationResult]:
        """Validate logical consistency of relationships (VAL-005)."""
        results = []
        
        # Build relationship pairs for checking contradictions
        rel_pairs: Dict[Tuple[str, str], Set[PredicateType]] = {}
        for rel in relationships:
            pair = tuple(sorted([rel.source_id, rel.target_id]))
            if pair not in rel_pairs:
                rel_pairs[pair] = set()
            rel_pairs[pair].add(rel.predicate)
        
        # Check for contradictory pairs
        for pair, predicates in rel_pairs.items():
            for contra_set in CONTRADICTORY_PAIRS:
                if contra_set.issubset(predicates):
                    results.append(ValidationResult(
                        rule_id="VAL-005",
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Contradictory relationships between {pair[0][:8]}... and {pair[1][:8]}...",
                        affected_entities=list(pair),
                        suggestion=f"Remove one of the contradictory relationship types: {contra_set}"
                    ))
        
        return results
    
    def _validate_confidence_scores(
        self,
        result: ExtractionResult,
        relationships: List[Relationship]
    ) -> List[ValidationResult]:
        """Validate that confidence scores are within reasonable bounds (VAL-006)."""
        results = []
        
        # Check entity confidence scores
        for entity in result.get_all_entities():
            confidence = getattr(entity, 'confidence', 0)
            
            if confidence < 0.5:
                results.append(ValidationResult(
                    rule_id="VAL-006",
                    passed=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Low confidence score ({confidence:.2f}) for entity {entity.id[:8]}...",
                    affected_entities=[entity.id],
                    suggestion="Review extraction or provide more context"
                ))
            
            if confidence < 0.0 or confidence > 1.0:
                results.append(ValidationResult(
                    rule_id="VAL-006",
                    passed=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid confidence score ({confidence}) for entity {entity.id[:8]}...",
                    affected_entities=[entity.id],
                    suggestion="Confidence must be between 0.0 and 1.0"
                ))
        
        # Check relationship confidence scores
        for rel in relationships:
            if rel.confidence < 0.5:
                results.append(ValidationResult(
                    rule_id="VAL-006",
                    passed=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Low confidence score ({rel.confidence:.2f}) for relationship {rel.id[:8]}...",
                    affected_relationships=[rel.id],
                    suggestion="Review extraction or provide more context"
                ))
            
            if rel.confidence < 0.0 or rel.confidence > 1.0:
                results.append(ValidationResult(
                    rule_id="VAL-006",
                    passed=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid confidence score ({rel.confidence}) for relationship {rel.id[:8]}...",
                    affected_relationships=[rel.id],
                    suggestion="Confidence must be between 0.0 and 1.0"
                ))
        
        return results
