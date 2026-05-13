"""Unit tests for Layer 1 Source Intelligence Skills.

Covers skill registry, skill output builders, and tenant isolation.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from skills import (
    SKILL_REGISTRY,
    BaseSkill,
    LicensingCompanyIntakeSkill,
    ProspectResearchSkill,
    SkillConfig,
    get_extraction_schema,
    get_skill,
)
from skills.licensing_company_intake import _LICENSING_COMPANY_EXTRACTION_SCHEMA
from skills.prospect_research import _PROSPECT_RESEARCH_EXTRACTION_SCHEMA


class TestSkillRegistry:
    """Skill registry lookup and resolution."""

    def test_registry_contains_both_skills(self):
        assert "licensing_company_intake" in SKILL_REGISTRY
        assert "prospect_research" in SKILL_REGISTRY
        assert len(SKILL_REGISTRY) == 2

    def test_get_skill_returns_instance(self):
        skill = get_skill("licensing_company_intake")
        assert skill is not None
        assert isinstance(skill, LicensingCompanyIntakeSkill)
        assert skill.skill_name == "licensing_company_intake"

    def test_get_skill_prospect_research(self):
        skill = get_skill("prospect_research")
        assert skill is not None
        assert isinstance(skill, ProspectResearchSkill)
        assert skill.skill_name == "prospect_research"

    def test_get_skill_generic_scrape_returns_none(self):
        assert get_skill("generic_scrape") is None

    def test_get_skill_unknown_returns_none(self):
        assert get_skill("unknown_skill") is None

    def test_get_skill_none_returns_none(self):
        assert get_skill(None) is None

    def test_get_extraction_schema_licensing(self):
        schema = get_extraction_schema("licensing_company_intake")
        assert schema is not None
        assert schema == _LICENSING_COMPANY_EXTRACTION_SCHEMA
        assert "discovered_themes" in schema["required"]

    def test_get_extraction_schema_prospect(self):
        schema = get_extraction_schema("prospect_research")
        assert schema is not None
        assert schema == _PROSPECT_RESEARCH_EXTRACTION_SCHEMA
        assert "company_profile" in schema["required"]

    def test_get_extraction_schema_generic_none(self):
        assert get_extraction_schema("generic_scrape") is None


class TestSkillConfig:
    """Skill configuration contracts."""

    def test_licensing_config_fields(self):
        skill = LicensingCompanyIntakeSkill()
        cfg = skill.config
        assert cfg.skill_name == "licensing_company_intake"
        assert cfg.target_entity_type == "licensing_company"
        assert cfg.output_contract == "SourceCorpus"
        assert "layer1.source_corpus.ready" in cfg.downstream_events
        assert "layer2.ontology_extraction.requested" in cfg.downstream_events
        assert len(cfg.required_source_types) > 0
        assert cfg.extraction_schema is not None

    def test_prospect_config_fields(self):
        skill = ProspectResearchSkill()
        cfg = skill.config
        assert cfg.skill_name == "prospect_research"
        assert cfg.target_entity_type == "sales_prospect"
        assert cfg.output_contract == "AccountIntelligencePacket"
        assert "layer1.account_intelligence.ready" in cfg.downstream_events
        assert "layer2.signal_extraction.requested" in cfg.downstream_events
        assert len(cfg.required_source_types) > 0
        assert cfg.extraction_schema is not None

    def test_skill_name_property(self):
        skill = LicensingCompanyIntakeSkill()
        assert skill.skill_name == "licensing_company_intake"

    def test_output_contract_property(self):
        skill = ProspectResearchSkill()
        assert skill.output_contract == "AccountIntelligencePacket"

    def test_downstream_events_property(self):
        skill = LicensingCompanyIntakeSkill()
        assert len(skill.downstream_events) == 2


class MockJob:
    """Minimal mock for ScrapingJob in builder tests."""

    def __init__(self, tenant_id: UUID, configuration: dict):
        self.id = uuid4()
        self.tenant_id = tenant_id
        self.configuration = configuration


class MockRawContent:
    """Minimal mock for RawContent."""

    def __init__(self, source_type: str = "product_page"):
        self.source_type = source_type


class MockExtractedData:
    """Minimal mock for ExtractedData."""

    def __init__(self, data: dict):
        self.data = data


class TestSourceCorpusBuilder:
    """LicensingCompanyIntakeSkill.build_output."""

    def test_build_output_basic(self):
        tenant_id = uuid4()
        job = MockJob(
            tenant_id=tenant_id,
            configuration={"company_name": "Allego", "company_id": "allego-123"},
        )
        raw_contents = [MockRawContent("product_page"), MockRawContent("case_study")]
        extracted_data = [
            MockExtractedData(
                {
                    "discovered_themes": ["sales enablement", "content governance"],
                    "source_evidence": [
                        {
                            "source_url": "https://allego.com/product",
                            "source_type": "product_page",
                            "confidence": "high",
                            "extracted_at": "2026-05-13T10:00:00Z",
                        }
                    ],
                }
            )
        ]

        skill = LicensingCompanyIntakeSkill()
        output = skill.build_output(job, raw_contents, extracted_data)

        assert output["tenant_id"] == str(tenant_id)
        assert output["company_name"] == "Allego"
        assert output["company_id"] == "allego-123"
        assert output["corpus_type"] == "licensing_company_ontology_seed"
        assert output["extraction_status"] == "ready_for_extraction"
        assert len(output["source_groups"]) == 2
        assert {"source_type": "product_page", "count": 1} in output["source_groups"]
        assert "sales enablement" in output["candidate_concepts"]
        assert len(output["provenance"]) == 1
        assert output["job_id"] == str(job.id)

    def test_build_output_empty(self):
        tenant_id = uuid4()
        job = MockJob(tenant_id=tenant_id, configuration={})
        skill = LicensingCompanyIntakeSkill()
        output = skill.build_output(job, [], [])

        assert output["company_name"] == "Unknown"
        assert output["company_id"] is None
        assert output["source_groups"] == []
        assert output["candidate_concepts"] == []


class TestAccountIntelligencePacketBuilder:
    """ProspectResearchSkill.build_output."""

    def test_build_output_basic(self):
        tenant_id = uuid4()
        job = MockJob(
            tenant_id=tenant_id,
            configuration={"account_name": "Acme Manufacturing", "account_id": "acme-456"},
        )
        raw_contents = []
        extracted_data = [
            MockExtractedData(
                {
                    "company_profile": {"size": "mid-market", "industry": "Manufacturing"},
                    "observed_signals": [
                        {
                            "signal": "Expanding dealer network",
                            "source": "press_release",
                            "confidence": "medium",
                            "detail": "Opened 3 new dealerships",
                        }
                    ],
                    "likely_pain_areas": ["distributed seller onboarding"],
                    "likely_stakeholders": ["CRO", "VP Sales"],
                    "source_evidence": [
                        {
                            "source_url": "https://acme.com/news",
                            "source_type": "press_release",
                            "confidence": "medium",
                        }
                    ],
                }
            )
        ]

        skill = ProspectResearchSkill()
        output = skill.build_output(job, raw_contents, extracted_data)

        assert output["tenant_id"] == str(tenant_id)
        assert output["account_name"] == "Acme Manufacturing"
        assert output["account_id"] == "acme-456"
        assert output["packet_type"] == "prospect_research"
        assert output["company_profile"]["size"] == "mid-market"
        assert len(output["observed_signals"]) == 1
        assert output["observed_signals"][0]["confidence"] == "medium"
        assert "distributed seller onboarding" in output["likely_pain_areas"]
        assert "CRO" in output["likely_stakeholders"]
        assert output["confidence_summary"]["signal_count"] == 1
        assert output["next_recommended_events"] == skill.downstream_events
        assert output["job_id"] == str(job.id)

    def test_build_output_empty(self):
        tenant_id = uuid4()
        job = MockJob(tenant_id=tenant_id, configuration={})
        skill = ProspectResearchSkill()
        output = skill.build_output(job, [], [])

        assert output["account_name"] == "Unknown"
        assert output["account_id"] is None
        assert output["observed_signals"] == []
        assert output["likely_pain_areas"] == []
        assert output["likely_stakeholders"] == []


class TestSkillSchemas:
    """JSON Schema validation for extraction schemas."""

    def test_licensing_schema_has_required_fields(self):
        schema = _LICENSING_COMPANY_EXTRACTION_SCHEMA
        assert schema["type"] == "object"
        assert "discovered_themes" in schema["required"]
        assert "candidate_capabilities" in schema["required"]
        assert "source_evidence" in schema["required"]
        assert "properties" in schema

    def test_prospect_schema_has_required_fields(self):
        schema = _PROSPECT_RESEARCH_EXTRACTION_SCHEMA
        assert schema["type"] == "object"
        assert "company_profile" in schema["required"]
        assert "observed_signals" in schema["required"]
        assert "likely_stakeholders" in schema["required"]
        assert "source_evidence" in schema["required"]


class TestSkillBaseClass:
    """Abstract base skill behavior."""

    def test_base_skill_is_abstract(self):
        with pytest.raises(TypeError):
            BaseSkill()

    def test_skill_subclass_requires_default_config(self):
        class BrokenSkill(BaseSkill):
            pass

        with pytest.raises(TypeError):
            BrokenSkill()
