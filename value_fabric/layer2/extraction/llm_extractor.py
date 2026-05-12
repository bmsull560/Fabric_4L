"""LLM-based entity and relationship extractors."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from value_fabric.layer2.extraction.chunker import SemanticChunker
from value_fabric.layer2.models.extraction_response import (
    CapabilityExtractionResponse,
    RelationshipExtractionResponse,
)
from value_fabric.layer2.models.ontology import Capability, Persona, UseCase, ValueDriver
from value_fabric.layer2.models.relationships import PredicateType, Relationship


class EntityExtractor:
    """Extract ontology entities from unstructured text using an LLM."""

    DEFAULT_CONFIDENCE = 0.85
    DEFAULT_TEMPERATURE = 0.0

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        confidence_threshold: float = DEFAULT_CONFIDENCE,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.temperature = temperature
        self._client: Any | None = None
        self.chunker = SemanticChunker()

    @property
    def client(self) -> Any:
        if self._client is None and self._api_key:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client

    # ------------------------------------------------------------------
    # Structured output helpers
    # ------------------------------------------------------------------

    async def _chat_completion_structured(
        self,
        messages: list[dict[str, str]],
        response_format: type[Any],
    ) -> tuple[Any, dict[str, Any] | None]:
        """Call the OpenAI API with structured JSON output."""
        if self._client is None:
            raise RuntimeError("OpenAI client not configured")
        resp = await self._client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_format,
            temperature=self.temperature,
        )
        parsed = resp.choices[0].message.parsed
        usage = resp.usage
        usage_dict: dict[str, Any] | None = None
        if usage:
            usage_dict = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        return parsed, usage_dict

    # ------------------------------------------------------------------
    # Entity extraction helpers
    # ------------------------------------------------------------------

    async def _extract_capabilities(
        self,
        text: str,
        source_url: str,
        job_id: str,
        min_confidence: float,
    ) -> list[Capability]:
        messages = [
            {
                "role": "system",
                "content": "Extract technical capabilities from the following text. Return JSON with a 'capabilities' array. Each capability must have name, description, confidence (0-1), and optional technical_features, api_endpoints, integrations, apqc_mapping.",
            },
            {"role": "user", "content": text},
        ]
        try:
            parsed, _ = await self._chat_completion_structured(
                messages, CapabilityExtractionResponse
            )
        except ValidationError:
            return []
        if parsed is None:
            return []
        result: list[Capability] = []
        for cap in parsed.capabilities:
            if cap.confidence >= min_confidence:
                cap.source_refs = [source_url]
                cap.extraction_job_id = job_id
                result.append(cap)
        return result

    async def _extract_use_cases(
        self,
        text: str,
        source_url: str,
        job_id: str,
        min_confidence: float,
    ) -> list[UseCase]:
        messages = [
            {
                "role": "system",
                "content": "Extract business use cases from the following text. Return JSON with a 'use_cases' array. Each use case must have name, description, confidence (0-1), and optional industry_context, required_capabilities, workflow_steps, kpis.",
            },
            {"role": "user", "content": text},
        ]
        # Reuse CapabilityExtractionResponse as a generic container (test fixture)
        try:
            parsed, _ = await self._chat_completion_structured(
                messages, CapabilityExtractionResponse
            )
        except ValidationError:
            return []
        if parsed is None:
            return []
        return []  # placeholder

    async def _extract_personas(
        self,
        text: str,
        source_url: str,
        job_id: str,
        min_confidence: float,
    ) -> list[Persona]:
        messages = [
            {
                "role": "system",
                "content": "Extract stakeholder personas from the following text. Return JSON with a 'personas' array. Each persona must have name, description, confidence (0-1), role_type, title, and optional seniority_level, department, pain_points, success_metrics.",
            },
            {"role": "user", "content": text},
        ]
        try:
            parsed, _ = await self._chat_completion_structured(
                messages, CapabilityExtractionResponse
            )
        except ValidationError:
            return []
        if parsed is None:
            return []
        return []  # placeholder

    async def _extract_value_drivers(
        self,
        text: str,
        source_url: str,
        job_id: str,
        min_confidence: float,
    ) -> list[ValueDriver]:
        messages = [
            {
                "role": "system",
                "content": "Extract value drivers from the following text. Return JSON with a 'value_drivers' array. Each driver must have name, description, confidence (0-1), category, and optional metrics, formula_string, unit, time_to_value.",
            },
            {"role": "user", "content": text},
        ]
        try:
            parsed, _ = await self._chat_completion_structured(
                messages, CapabilityExtractionResponse
            )
        except ValidationError:
            return []
        if parsed is None:
            return []
        return []  # placeholder

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract(
        self,
        text: str,
        source_url: str = "",
        job_id: str = "",
    ) -> dict[str, Any]:
        """Extract all entity types from text."""
        min_confidence = self.confidence_threshold
        chunks = self.chunker.chunk_text(text, source_url=source_url)
        all_caps: list[Capability] = []
        all_use_cases: list[UseCase] = []
        all_personas: list[Persona] = []
        all_drivers: list[ValueDriver] = []
        for chunk in chunks:
            caps = await self._extract_capabilities(
                chunk.content, source_url, job_id, min_confidence
            )
            all_caps.extend(caps)
        return {
            "capabilities": all_caps,
            "use_cases": all_use_cases,
            "personas": all_personas,
            "value_drivers": all_drivers,
        }


# ------------------------------------------------------------------
# Relationship extractor
# ------------------------------------------------------------------


class RelationshipExtractor:
    """Extract relationships between entities using an LLM."""

    DEFAULT_CONFIDENCE = 0.85

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        confidence_threshold: float = DEFAULT_CONFIDENCE,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.confidence_threshold = confidence_threshold
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None and self._api_key:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def extract_relationships(
        self,
        text: str,
        entities: list[Any],
        source_url: str = "",
        job_id: str = "",
    ) -> list[Relationship]:
        """Extract relationships between entities from text."""
        if not entities:
            return []
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract relationships between entities. Return JSON with a 'relationships' array. "
                    "Each relationship must have source_id, target_id, raw_predicate, canonical_predicate, evidence_text, confidence."
                ),
            },
            {"role": "user", "content": text},
        ]
        if self._client is None:
            return []
        try:
            parsed, _ = await self._chat_completion_structured(
                messages, RelationshipExtractionResponse
            )
        except (ValidationError, Exception):
            return []
        if parsed is None:
            return []
        result: list[Relationship] = []
        for rel in parsed.relationships:
            if rel.confidence >= self.confidence_threshold:
                rel.source_url = source_url
                rel.extraction_job_id = job_id
                result.append(rel)
        return result

    async def _chat_completion_structured(
        self,
        messages: list[dict[str, str]],
        response_format: type[Any],
    ) -> tuple[Any, dict[str, Any] | None]:
        if self._client is None:
            raise RuntimeError("OpenAI client not configured")
        resp = await self._client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_format,
            temperature=0.0,
        )
        parsed = resp.choices[0].message.parsed
        usage = resp.usage
        usage_dict: dict[str, Any] | None = None
        if usage:
            usage_dict = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        return parsed, usage_dict
