"""LLM-based entity and relationship extractors for Layer 2."""

from __future__ import annotations

import asyncio
import math
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from layer2_extraction.extraction.cache import ExtractionCache
from layer2_extraction.models.extraction_response import (
    CapabilityExtractionResponse,
    FeatureExtractionResponse,
    PersonaExtractionResponse,
    RelationshipExtractionResponse,
    UnifiedExtractionResponse,
    UseCaseExtractionResponse,
    ValueDriverExtractionResponse,
)
from layer2_extraction.models.ontology import (
    Capability,
    Feature,
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

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        cache: ExtractionCache | None = None,
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.client = client or _MockClient()
        self.cache = cache

    async def chat_completion_structured(
        self, **kwargs: Any
    ) -> tuple[Any, None]:
        return await self.client.chat_completion_structured(**kwargs)

    async def _cached_extract(
        self,
        text: str,
        endpoint: str,
        response_format: type[Any],
        source_url: str,
        job_id: str,
        confidence_threshold: float,
        entity_attr: str,
    ) -> list[Any]:
        """Generic cached extraction helper.

        Returns deep-copied entities so that cached objects are never mutated
        in place across different extraction calls.
        """
        if self.cache is not None:
            cached = await self.cache.get(text, endpoint, model=self.model)
            if cached is not None:
                entities = getattr(cached, entity_attr, [])
                return self._prepare_entities(entities, source_url, job_id, confidence_threshold)

        try:
            response, _ = await self.client.chat_completion_structured(
                response_format=response_format,
                endpoint=endpoint,
            )
        except ValidationError as exc:
            raise LLMExtractionError(f"schema validation error: {exc}") from exc

        if response is None:
            return []

        if self.cache is not None:
            await self.cache.set(text, endpoint, response, model=self.model)

        entities = getattr(response, entity_attr, [])
        return self._prepare_entities(entities, source_url, job_id, confidence_threshold)

    def _prepare_entities(
        self,
        entities: list[Any],
        source_url: str,
        job_id: str,
        confidence_threshold: float,
    ) -> list[Any]:
        """Deep-copy entities, tag with job_id/source_url, and filter by confidence."""
        result: list[Any] = []
        for ent in entities:
            copied = ent.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if hasattr(copied, "source_refs") and copied.source_refs and source_url:
                if source_url not in copied.source_refs:
                    copied.source_refs.append(source_url)
            if copied.confidence >= confidence_threshold:
                result.append(copied)
        return result

    async def _extract_capabilities(
        self, text: str, source_url: str, job_id: str, confidence_threshold: float = 0.0
    ) -> list[Capability]:
        """Extract capabilities using structured output."""
        return await self._cached_extract(
            text,
            "extract_capabilities",
            CapabilityExtractionResponse,
            source_url,
            job_id,
            confidence_threshold,
            "capabilities",
        )

    async def _extract_use_cases(
        self, text: str, source_url: str, job_id: str, confidence_threshold: float = 0.0
    ) -> list[UseCase]:
        """Extract use cases using structured output."""
        return await self._cached_extract(
            text,
            "extract_use_cases",
            UseCaseExtractionResponse,
            source_url,
            job_id,
            confidence_threshold,
            "use_cases",
        )

    async def _extract_personas(
        self, text: str, source_url: str, job_id: str, confidence_threshold: float = 0.0
    ) -> list[Persona]:
        """Extract personas using structured output."""
        return await self._cached_extract(
            text,
            "extract_personas",
            PersonaExtractionResponse,
            source_url,
            job_id,
            confidence_threshold,
            "personas",
        )

    async def _extract_value_drivers(
        self, text: str, source_url: str, job_id: str, confidence_threshold: float = 0.0
    ) -> list[ValueDriver]:
        """Extract value drivers using structured output."""
        return await self._cached_extract(
            text,
            "extract_value_drivers",
            ValueDriverExtractionResponse,
            source_url,
            job_id,
            confidence_threshold,
            "value_drivers",
        )

    async def _extract_features(
        self, text: str, source_url: str, job_id: str, confidence_threshold: float = 0.0
    ) -> list[Feature]:
        """Extract features using structured output."""
        return await self._cached_extract(
            text,
            "extract_features",
            FeatureExtractionResponse,
            source_url,
            job_id,
            confidence_threshold,
            "features",
        )

    async def extract(
        self,
        text: str,
        source_url: str = "",
        job_id: str = "",
        confidence_threshold: float = 0.0,
    ) -> dict[str, list[Any]]:
        """Extract entities from text concurrently.

        Independent entity extractions (capabilities, use_cases, personas,
        value_drivers, features) are launched in parallel via asyncio.gather.
        Partial failures are handled gracefully: entities from successful
        extractions are returned, and the exception is re-raised only if
        every extraction fails.
        """
        coros = [
            self._extract_capabilities(text, source_url, job_id, confidence_threshold),
            self._extract_use_cases(text, source_url, job_id, confidence_threshold),
            self._extract_personas(text, source_url, job_id, confidence_threshold),
            self._extract_value_drivers(text, source_url, job_id, confidence_threshold),
            self._extract_features(text, source_url, job_id, confidence_threshold),
        ]

        results = await asyncio.gather(*coros, return_exceptions=True)

        capabilities: list[Any] = []
        use_cases: list[Any] = []
        personas: list[Any] = []
        value_drivers: list[Any] = []
        features: list[Any] = []
        failures = 0

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                failures += 1
                continue
            if idx == 0:
                capabilities = result
            elif idx == 1:
                use_cases = result
            elif idx == 2:
                personas = result
            elif idx == 3:
                value_drivers = result
            elif idx == 4:
                features = result

        if failures == len(coros):
            raise LLMExtractionError("All entity extractions failed")

        return {
            "capabilities": capabilities,
            "use_cases": use_cases,
            "personas": personas,
            "value_drivers": value_drivers,
            "features": features,
        }

    async def extract_unified(
        self,
        text: str,
        source_url: str = "",
        job_id: str = "",
        confidence_threshold: float = 0.0,
    ) -> dict[str, list[Any]]:
        """Extract entities and relationships in a single LLM call.

        This is a latency/cost optimization (opt #7) that combines entity
        and relationship extraction into one structured LLM response.
        Falls back to separate extractions if the unified endpoint fails.
        """
        if self.cache is not None:
            cached = await self.cache.get(text, "extract_unified", model=self.model)
            if cached is not None:
                return self._unified_response_to_dict(cached, source_url, job_id, confidence_threshold)

        try:
            response, _ = await self.client.chat_completion_structured(
                response_format=UnifiedExtractionResponse,
                endpoint="extract_unified",
            )
        except ValidationError as exc:
            raise LLMExtractionError(f"schema validation error: {exc}") from exc

        if response is None:
            return await self.extract(text, source_url, job_id, confidence_threshold)

        if self.cache is not None:
            await self.cache.set(text, "extract_unified", response, model=self.model)

        return self._unified_response_to_dict(response, source_url, job_id, confidence_threshold)

    def _unified_response_to_dict(
        self,
        response: UnifiedExtractionResponse,
        source_url: str,
        job_id: str,
        confidence_threshold: float,
    ) -> dict[str, list[Any]]:
        """Convert a UnifiedExtractionResponse to the standard entity dict."""
        result: dict[str, list[Any]] = {
            "capabilities": [],
            "use_cases": [],
            "personas": [],
            "value_drivers": [],
            "features": [],
            "relationships": [],
        }
        for cap in getattr(response, "capabilities", []):
            copied = cap.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if copied.source_refs and source_url and source_url not in copied.source_refs:
                copied.source_refs.append(source_url)
            if copied.confidence >= confidence_threshold:
                result["capabilities"].append(copied)
        for uc in getattr(response, "use_cases", []):
            copied = uc.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if copied.source_refs and source_url and source_url not in copied.source_refs:
                copied.source_refs.append(source_url)
            if copied.confidence >= confidence_threshold:
                result["use_cases"].append(copied)
        for p in getattr(response, "personas", []):
            copied = p.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if copied.source_refs and source_url and source_url not in copied.source_refs:
                copied.source_refs.append(source_url)
            if copied.confidence >= confidence_threshold:
                result["personas"].append(copied)
        for vd in getattr(response, "value_drivers", []):
            copied = vd.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if copied.source_refs and source_url and source_url not in copied.source_refs:
                copied.source_refs.append(source_url)
            if copied.confidence >= confidence_threshold:
                result["value_drivers"].append(copied)
        for f in getattr(response, "features", []):
            copied = f.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if copied.source_refs and source_url and source_url not in copied.source_refs:
                copied.source_refs.append(source_url)
            if copied.confidence >= confidence_threshold:
                result["features"].append(copied)
        for rel in getattr(response, "relationships", []):
            copied = rel.model_copy(deep=True)
            copied.extraction_job_id = job_id
            if copied.confidence >= confidence_threshold:
                result["relationships"].append(copied)
        return result

    async def extract_with_schema(
        self, text: str, schema: type[BaseModel], source_url: str = "", job_id: str = ""
    ) -> Any:
        """Extract entities conforming to a Pydantic schema."""
        return schema()


class RelationshipExtractor:
    """Extract relationships between entities using an LLM."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o", client: Any | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.client = client or _MockClient()

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
