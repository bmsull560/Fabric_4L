"""Ontology models for Layer 2 extraction."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RoleType(str, Enum):
    ECONOMIC_BUYER = "economic_buyer"
    CHAMPION = "champion"
    OPERATIONAL_USER = "operational_user"
    TECHNICAL_BUYER = "technical_buyer"
    STAKEHOLDER = "stakeholder"


class SeniorityLevel(str, Enum):
    EXECUTIVE_SPONSOR = "executive_sponsor"
    C_SUITE = "c_suite"
    VP = "vp"
    DIRECTOR = "director"
    MANAGER = "manager"
    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    UNKNOWN = "unknown"


class ValueCategory(str, Enum):
    CAPITAL_EFFICIENCY = "capital_efficiency"
    COST_REDUCTION = "cost_reduction"
    RISK_MITIGATION = "risk_mitigation"
    REVENUE_ENHANCEMENT = "revenue_enhancement"
    REVENUE = "revenue"
    COST = "cost"
    RISK = "risk"
    CAPITAL = "capital"


class EnablementType(str, Enum):
    REQUIRED = "required"
    ENHANCES = "enhances"
    OPTIONAL = "optional"


class BenefitType(str, Enum):
    TIME_SAVINGS = "time_savings"
    ERROR_REDUCTION = "error_reduction"
    VISIBILITY = "visibility"
    EFFICIENCY = "efficiency"


class DriverType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class ImpactLevel(str, Enum):
    TRANSFORMATIONAL = "transformational"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINOR = "minor"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OntologyEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_refs: list[str] = Field(default_factory=list)
    extraction_job_id: str | None = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def _validate_description(cls, v: str) -> str:
        if not v or len(v.strip()) <= 5:
            raise ValueError("Description must be at least 5 characters")
        return v.strip()


class Capability(OntologyEntity):
    category: str = ""
    parent_capability: str | None = None

    @model_validator(mode="after")
    def _check_name_not_empty(self) -> "Capability":
        if not self.name or not self.name.strip():
            raise ValueError("Capability name cannot be empty")
        return self

    technical_features: list[str] = Field(default_factory=list)
    api_endpoints: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    apqc_mapping: list[str] = Field(default_factory=list)
    implementation_status: str = Field(default="planned")
    technical_spec: str | None = None
    parent_capability_id: str | None = None

    @field_validator("implementation_status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"planned", "beta", "ga", "deprecated"}
        if v not in allowed:
            raise ValueError(f"implementation_status must be one of {allowed}")
        return v


class Persona(OntologyEntity):
    role_type: RoleType
    seniority_level: SeniorityLevel = Field(default=SeniorityLevel.UNKNOWN)
    title: str
    department: str = ""
    pain_points: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _auto_fill_name_description(cls, data: Any) -> Any:
        if isinstance(data, dict):
            name = data.get("name")
            if name is None or (isinstance(name, str) and not name.strip()):
                data["name"] = data.get("title", "") or "Unknown"
            desc = data.get("description")
            if desc is None or (isinstance(desc, str) and (not desc.strip() or len(desc.strip()) < 5)):
                title = data.get("title", "")
                role = data.get("role_type", "")
                desc_val = f"{title} - {role}" if title and role else (title or "Persona description")
                if len(desc_val) < 5:
                    desc_val = f"{desc_val} profile"
                data["description"] = desc_val
        return data


class Feature(OntologyEntity):
    category: str = ""
    implementation_status: str = Field(default="planned")
    technical_spec: str | None = None
    parent_capability_id: str | None = None

    @field_validator("implementation_status")
    @classmethod
    def _validate_status(cls, v: str) -> str:
        allowed = {"planned", "beta", "ga", "deprecated"}
        if v not in allowed:
            raise ValueError(f"implementation_status must be one of {allowed}")
        return v


class UseCase(OntologyEntity):
    industry_context: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    workflow_steps: list[str] = Field(default_factory=list)
    kpis: list[str] = Field(default_factory=list)


class ValueDriver(OntologyEntity):
    category: ValueCategory
    metrics: list[str] = Field(default_factory=list)
    formula_string: str | None = None
    unit: str | None = None
    time_to_value: str | None = None

    @field_validator("formula_string")
    @classmethod
    def _validate_formula(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[\w\s\+\-\*\/\(\)\{\}\.\,\%]+$", v):
            raise ValueError("Formula contains illegal characters")
        return v


class APQCProcess(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pcf_id: str
    process_name: str
    hierarchy_level: int = Field(default=1, ge=1, le=5)
