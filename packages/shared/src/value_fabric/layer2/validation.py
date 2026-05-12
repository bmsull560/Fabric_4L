"""Ontology validation utilities for Layer 2 extraction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    rule_id: str
    severity: ValidationSeverity
    passed: bool
    message: str = ""
    entity_id: str | None = None


class EntailmentValidator:
    """Validates ontology entailments and constraints."""

    def validate(self, result: Any, relationships: list[Any]) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        entities: list[Any] = []

        # Collect entities from ExtractionResult
        for attr in ("capabilities", "personas", "use_cases", "value_drivers", "features"):
            entities.extend(getattr(result, attr, []) or [])

        # VAL-001: required properties
        for entity in entities:
            if hasattr(entity, "name") and (not entity.name or not entity.name.strip()):
                results.append(
                    ValidationResult(
                        rule_id="VAL-001",
                        severity=ValidationSeverity.ERROR,
                        passed=False,
                        message="Name is required",
                        entity_id=getattr(entity, "id", None),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        rule_id="VAL-001",
                        severity=ValidationSeverity.ERROR,
                        passed=True,
                        message="Name present",
                        entity_id=getattr(entity, "id", None),
                    )
                )

        # VAL-006: confidence bounds
        for entity in entities:
            if hasattr(entity, "confidence") and entity.confidence is not None:
                if entity.confidence < 0.0 or entity.confidence > 1.0:
                    results.append(
                        ValidationResult(
                            rule_id="VAL-006",
                            severity=ValidationSeverity.ERROR,
                            passed=False,
                            message=f"Confidence {entity.confidence} out of bounds [0.0, 1.0]",
                            entity_id=getattr(entity, "id", None),
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            rule_id="VAL-006",
                            severity=ValidationSeverity.ERROR,
                            passed=True,
                            message="Confidence valid",
                            entity_id=getattr(entity, "id", None),
                        )
                    )

        # VAL-002: domain/range constraints
        for rel in relationships:
            # Simple heuristic: Persona should not be source of ENABLES
            source_type = getattr(rel, "source_type", None)
            target_type = getattr(rel, "target_type", None)
            pred = getattr(rel, "canonical_predicate", None) or getattr(rel, "predicate", None)
            if pred and getattr(pred, "value", pred) == "enables":
                # Check if source is a Persona ( heuristic: has role_type )
                # Since we don't have entity type directly on relationship,
                # we infer from the result entities
                source_id = getattr(rel, "source_id", None)
                source_entity = next((e for e in entities if getattr(e, "id", None) == source_id), None)
                if source_entity and hasattr(source_entity, "role_type"):
                    results.append(
                        ValidationResult(
                            rule_id="VAL-002",
                            severity=ValidationSeverity.ERROR,
                            passed=False,
                            message="Persona cannot be source of ENABLES relationship",
                            entity_id=source_id,
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            rule_id="VAL-002",
                            severity=ValidationSeverity.ERROR,
                            passed=True,
                            message="Domain/range valid",
                        )
                    )
            else:
                results.append(
                    ValidationResult(
                        rule_id="VAL-002",
                        severity=ValidationSeverity.ERROR,
                        passed=True,
                        message="Domain/range valid",
                    )
                )

        return results

    def validate_domain_range(self, relationship: Any) -> list[ValidationResult]:
        return []

    def validate_confidence(self, entity: Any, min_confidence: float = 0.0) -> list[ValidationResult]:
        return []
