"""Validation layer for extracted entities and relationships."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..models.ontology import Capability, Persona, UseCase, ValueDriver
from ..models.relationships import PredicateType, Relationship


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    rule_id: str
    severity: ValidationSeverity
    passed: bool
    message: str = ""


class EntailmentValidator:
    """Validate extraction results and relationships against ontology constraints."""

    def validate(
        self, result: Any, relationships: list[Relationship]
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []

        # VAL-001: Required properties validation
        for vd in getattr(result, "value_drivers", []) or []:
            if isinstance(vd, ValueDriver) and not getattr(vd, "unit", None):
                results.append(
                    ValidationResult(
                        rule_id="VAL-001",
                        severity=ValidationSeverity.ERROR,
                        passed=False,
                        message="ValueDriver missing required unit",
                    )
                )

        # VAL-006: Confidence score bounds
        for entity in self._all_entities(result):
            conf = getattr(entity, "confidence", 0.0)
            if not (0.0 <= conf <= 1.0):
                results.append(
                    ValidationResult(
                        rule_id="VAL-006",
                        severity=ValidationSeverity.ERROR,
                        passed=False,
                        message=f"Confidence {conf} out of bounds [0, 1]",
                    )
                )

        # VAL-002: Domain/range constraints
        for rel in relationships:
            if rel.canonical_predicate == PredicateType.ENABLES:
                source = self._find_entity_by_id(result, rel.source_id)
                if source is not None and not isinstance(source, Capability):
                    results.append(
                        ValidationResult(
                            rule_id="VAL-002",
                            severity=ValidationSeverity.ERROR,
                            passed=False,
                            message="Domain violation: only Capability can ENABLES",
                        )
                    )
                target = self._find_entity_by_id(result, rel.target_id)
                if target is not None and not isinstance(target, UseCase):
                    results.append(
                        ValidationResult(
                            rule_id="VAL-002",
                            severity=ValidationSeverity.ERROR,
                            passed=False,
                            message="Range violation: ENABLES must target UseCase",
                        )
                    )

        if not results:
            results.append(
                ValidationResult(
                    rule_id="VAL-000",
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message="All validations passed",
                )
            )

        return results

    def _all_entities(self, result: Any) -> list[Any]:
        entities: list[Any] = []
        for attr in ("capabilities", "features", "use_cases", "personas", "value_drivers"):
            entities.extend(getattr(result, attr, []) or [])
        return entities

    def _find_entity_by_id(self, result: Any, entity_id: str) -> Any | None:
        for entity in self._all_entities(result):
            if getattr(entity, "id", None) == entity_id:
                return entity
        return None
