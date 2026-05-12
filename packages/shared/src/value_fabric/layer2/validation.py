"""Ontology validation utilities for Layer 2 extraction."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EntailmentValidator:
    """Validates ontology entailments and constraints."""

    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = []

    def add_rule(
        self,
        property_name: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        required: bool = True,
    ) -> None:
        self._rules.append(
            {
                "property_name": property_name,
                "severity": severity,
                "required": required,
            }
        )

    def validate(self, entity: Any, min_confidence: float = 0.0) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        for rule in self._rules:
            prop = rule["property_name"]
            if rule["required"] and (not hasattr(entity, prop) or getattr(entity, prop) is None):
                errors.append(
                    {
                        "property": prop,
                        "severity": rule["severity"],
                        "message": f"Required property '{prop}' is missing",
                    }
                )
        errors.extend(self.validate_confidence(entity, min_confidence))
        return errors

    def validate_domain_range(self, relationship: Any) -> list[dict[str, Any]]:
        return []

    def validate_confidence(self, entity: Any, min_confidence: float = 0.0) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        if hasattr(entity, "confidence") and entity.confidence is not None:
            if entity.confidence < min_confidence:
                errors.append(
                    {
                        "property": "confidence",
                        "severity": ValidationSeverity.WARNING,
                        "message": f"Confidence {entity.confidence} below threshold {min_confidence}",
                    }
                )
        return errors
