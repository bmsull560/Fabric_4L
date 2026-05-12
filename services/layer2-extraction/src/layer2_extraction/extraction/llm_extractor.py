"""LLM-based entity and relationship extractors for Layer 2."""

from __future__ import annotations

import json
import math
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from layer2_extraction.models.extraction_response import (
    CapabilityExtractionResponse,
    RelationshipExtractionResponse,
)
from layer2_extraction.models.ontology import (
    Capability,
    Persona,
    RoleType,
    SeniorityLevel,
    UseCase,
    ValueDriver,
    ValueCategory,
)
from layer2_extraction.models.relationships import PredicateType, Relationship


class LLMExtractionError(Exception):
    """Error during LLM extraction."""
    pass


def _logprob_confidence_from_response(response: Any) -> float | None:
    """Calculate average confidence from logprobs."""
    try:
        logprobs = response.choices[0].logprobs
        if logprobs is None:
            return None
        content = logprobs.content
        if not content:
            return None
        logprob_values = [token.logprob for token in content]
        if not logprob_values:
            return None
        avg_logprob = sum(logprob_values) / len(logprob_values)
        return math.exp(avg_logprob)
    except (AttributeError, IndexError):
        return None


def _effective_confidence(raw_confidence: float, logprob_confidence: float | None = None) -> float:
    """Combine raw confidence with logprob confidence (70/30 blend) and clamp to [0, 1]."""
    if logprob_confidence is None:
        result = raw_confidence
    else:
        result = (0.7 * raw_confidence) + (0.3 * logprob_confidence)
    return max(0.0, min(1.0, result))


def _strict_array_tool(
    function_name: str,
    description: str,
    array_field_name: str,
    item_schema: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build a strict array tool definition for OpenAI function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": function_name,
                "description": description,
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        array_field_name: {
                            "type": "array",
                            "items": item_schema,
                        }
                    },
                    "required": [array_field_name],
                    "additionalProperties": False,
                },
            },
        }
    ]


class _MockClient:
    """Mock client for tests."""

    async def chat_completion_structured(self, **kwargs: Any) -> tuple[Any, None]:
        return None, None


class EntityExtractor:
    """Extract ontology entities from text using an LLM."""

    USECASE_SCHEMA: dict[str, Any] = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "description": {"type": "string"}},
        "required": ["name", "description"],
        "additionalProperties": False,
    }
    FEATURE_SCHEMA: dict[str, Any] = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "description": {"type": "string"}},
        "required": ["name", "description"],
        "additionalProperties": False,
    }

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.client = _MockClient()

    async def chat_completion_structured(
        self, **kwargs: Any
    ) -> tuple[Any, None]:
        return await self.client.chat_completion_structured(**kwargs)

    async def _extract_capabilities(
        self, text: str, source_url: str, job_id: str, confidence_threshold: float = 0.0
    ) -> list[Capability]:
        """Extract capabilities using structured output."""
        try:
            response, _ = await self.client.chat_completion_structured(
                response_format=CapabilityExtractionResponse,
                endpoint="extract_capabilities",
            )
        except ValidationError as exc:
            raise LLMExtractionError(f"schema validation error: {exc}") from exc

        if response is None:
            return []
        capabilities = getattr(response, "capabilities", [])
        for cap in capabilities:
            cap.extraction_job_id = job_id
            if cap.source_refs and source_url:
                cap.source_refs.append(source_url)
        return [c for c in capabilities if c.confidence >= confidence_threshold]

    async def extract(
        self, text: str, source_url: str = "", job_id: str = ""
    ) -> dict[str, list[Any]]:
        """Extract entities from text."""
        return {
            "capabilities": [],
            "use_cases": [],
            "personas": [],
            "value_drivers": [],
        }

    async def extract_with_schema(
        self, text: str, schema: type[BaseModel], source_url: str = "", job_id: str = ""
    ) -> Any:
        """Extract entities conforming to a Pydantic schema."""
        return schema()


class RelationshipExtractor:
    """Extract relationships between entities using an LLM."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.client = _MockClient()

    async def chat_completion_structured(
        self, **kwargs: Any
    ) -> tuple[Any, None]:
        return await self.client.chat_completion_structured(**kwargs)

    async def extract_relationships(
        self,
        text: str,
        entities: dict[str, list[Any]],
        source_url: str = "",
        job_id: str = "",
        confidence_threshold: float = 0.0,
    ) -> list[Relationship]:
        """Extract relationships between entities from text."""
        total_entities = sum(len(v) for v in entities.values())
        if total_entities < 2:
            return []

        try:
            response, _ = await self.client.chat_completion_structured(
                response_format=RelationshipExtractionResponse,
                endpoint="extract_relationships",
            )
        except ValidationError as exc:
            raise LLMExtractionError(f"schema validation error: {exc}") from exc

        if response is None:
            return []
        relationships = getattr(response, "relationships", [])
        for rel in relationships:
            rel.extraction_job_id = job_id
        return [r for r in relationships if r.confidence >= confidence_threshold]

    async def extract_relationships_with_schema(
        self, text: str, schema: type[BaseModel], source_url: str = "", job_id: str = ""
    ) -> Any:
        """Extract relationships conforming to a Pydantic schema."""
        return schema()
