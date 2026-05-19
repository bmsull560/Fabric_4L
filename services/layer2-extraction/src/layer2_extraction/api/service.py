"""Layer 2 extraction API service layer."""

from __future__ import annotations

from layer2_extraction.extraction.chunker import SemanticChunker
from layer2_extraction.extraction.llm_extractor import EntityExtractor, RelationshipExtractor
from layer2_extraction.models.extraction_api import ExtractionResult


class ExtractionService:
    """Orchestrates the full extraction pipeline."""

    def __init__(self, api_key: str | None = None) -> None:
        self.chunker = SemanticChunker()
        self.entity_extractor = EntityExtractor(api_key=api_key)
        self.relationship_extractor = RelationshipExtractor(api_key=api_key)

    async def extract(
        self,
        content: str,
        source_url: str = "",
        job_id: str = "",
    ) -> ExtractionResult:
        """Run full extraction pipeline on content."""
        chunks = self.chunker.chunk_text(content, source_url=source_url)
        result = ExtractionResult(source_url=source_url)

        for chunk in chunks:
            entities = await self.entity_extractor.extract(
                chunk.content, source_url=source_url, job_id=job_id
            )
            result.capabilities.extend(entities.get("capabilities", []))
            result.use_cases.extend(entities.get("use_cases", []))
            result.personas.extend(entities.get("personas", []))
            result.value_drivers.extend(entities.get("value_drivers", []))

        all_entities = result.get_all_entities()
        relationships = await self.relationship_extractor.extract_relationships(
            content, all_entities, source_url=source_url, job_id=job_id
        )
        result.relationships = relationships
        return result
