"""Extended tests for EntityDeduplicator pure-logic methods.

Covers logic that does not require an OpenAI connection:
- _compute_similarity_matrix()
- _select_canonical()
- _entity_to_text()
- _merge_into_canonical() (and the type-specific merge helpers)

Uses sys.path manipulation so the deduplicator and the ontology models share
the exact same module objects — needed for isinstance() checks inside merge
helpers to pass correctly.
"""

import sys
from pathlib import Path
from uuid import uuid4

import numpy as np

# ---------------------------------------------------------------------------
# Add layer2 src to sys.path so all imports share the same module objects.
# The openai stub must be registered first (conftest.py does this at
# collection time, but we guard here so the file is also runnable standalone).
# ---------------------------------------------------------------------------
_layer2_src = str(Path(__file__).resolve().parents[1] / "src")
if _layer2_src not in sys.path:
    sys.path.insert(0, _layer2_src)

if "openai" not in sys.modules:
    import types as _types
    _openai = _types.ModuleType("openai")
    _openai.AsyncOpenAI = type("AsyncOpenAI", (), {})
    sys.modules["openai"] = _openai

# Now import normally — deduplicator and ontology share the same class objects.
from layer2_extraction.extraction.deduplicator import EntityDeduplicator  # noqa: E402
from layer2_extraction.models.ontology import (  # noqa: E402
    Capability,
    Feature,
    Persona,
    RoleType,
    SeniorityLevel,
    UseCase,
    ValueCategory,
    ValueDriver,
)


# ---------------------------------------------------------------------------
# Helper: instantiate EntityDeduplicator without touching OpenAI
# ---------------------------------------------------------------------------

def _make_dedup(threshold: float = 0.85) -> EntityDeduplicator:
    obj = object.__new__(EntityDeduplicator)
    obj.threshold = threshold
    return obj


# ---------------------------------------------------------------------------
# Entity factories
# ---------------------------------------------------------------------------

def _capability(
    name: str = "Real-Time Ingestion",
    desc: str = "Stream data from multiple sources.",
    features: list[str] | None = None,
    source_refs: list[str] | None = None,
    confidence: float = 0.8,
) -> Capability:
    return Capability(
        name=name,
        description=desc,
        technical_features=features if features is not None else ["Kafka", "CDC"],
        source_refs=source_refs if source_refs is not None else ["https://example.com"],
        confidence=confidence,
    )


def _use_case(
    name: str = "Automated Reconciliation",
    desc: str = "Automate reconciliation across multiple ledgers.",
    industries: list[str] | None = None,
    source_refs: list[str] | None = None,
    confidence: float = 0.75,
) -> UseCase:
    return UseCase(
        name=name,
        description=desc,
        industry_context=industries or ["Finance"],
        confidence=confidence,
    )


def _persona(
    title: str = "CFO",
    department: str = "Finance",
    pain_points: list[str] | None = None,
    confidence: float = 0.9,
) -> Persona:
    return Persona(
        role_type=RoleType.ECONOMIC_BUYER,
        title=title,
        department=department,
        pain_points=pain_points or ["Budget overruns"],
        confidence=confidence,
    )


def _value_driver(
    name: str = "Cost Reduction",
    desc: str = "Reduce operational costs through automation.",
    metrics: list[str] | None = None,
    confidence: float = 0.85,
) -> ValueDriver:
    return ValueDriver(
        category=ValueCategory.COST_REDUCTION,
        name=name,
        description=desc,
        unit="USD",
        metrics=metrics or ["FTE savings"],
        confidence=confidence,
    )


def _feature(
    name: str = "Auto-Reconcile",
    desc: str = "Automatically reconcile entries using AI matching.",
    status: str = "ga",
    spec: str | None = None,
    confidence: float = 0.88,
) -> Feature:
    return Feature(
        name=name,
        description=desc,
        implementation_status=status,
        technical_spec=spec,
        source_refs=[],
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# _compute_similarity_matrix
# ---------------------------------------------------------------------------

class TestComputeSimilarityMatrix:
    def setup_method(self):
        self.dedup = _make_dedup()

    def test_diagonal_is_ones(self):
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        sim = self.dedup._compute_similarity_matrix(embeddings)
        np.testing.assert_allclose(np.diag(sim), [1.0, 1.0, 1.0], atol=1e-6)

    def test_orthogonal_vectors_similarity_zero(self):
        embeddings = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
        ])
        sim = self.dedup._compute_similarity_matrix(embeddings)
        assert abs(sim[0][1]) < 1e-6
        assert abs(sim[1][0]) < 1e-6

    def test_identical_vectors_similarity_one(self):
        v = np.array([3.0, 4.0])  # non-unit vector
        embeddings = np.array([v, v])
        sim = self.dedup._compute_similarity_matrix(embeddings)
        np.testing.assert_allclose(sim[0][1], 1.0, atol=1e-6)

    def test_matrix_is_symmetric(self):
        embeddings = np.random.default_rng(42).random((4, 8))
        sim = self.dedup._compute_similarity_matrix(embeddings)
        np.testing.assert_allclose(sim, sim.T, atol=1e-6)

    def test_values_in_range_minus1_to_plus1(self):
        embeddings = np.random.default_rng(0).random((5, 10)) - 0.5
        sim = self.dedup._compute_similarity_matrix(embeddings)
        assert sim.min() >= -1.0 - 1e-6
        assert sim.max() <= 1.0 + 1e-6

    def test_single_vector_returns_1x1_matrix(self):
        embeddings = np.array([[1.0, 2.0, 3.0]])
        sim = self.dedup._compute_similarity_matrix(embeddings)
        assert sim.shape == (1, 1)
        assert abs(sim[0][0] - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# _select_canonical
# ---------------------------------------------------------------------------

class TestSelectCanonical:
    def setup_method(self):
        self.dedup = _make_dedup()

    def test_selects_entity_with_most_source_refs(self):
        e1 = _capability(source_refs=["url1"], confidence=0.5)
        e2 = _capability(source_refs=["url1", "url2", "url3"], confidence=0.5)
        e3 = _capability(source_refs=["url1", "url2"], confidence=0.5)
        canonical = self.dedup._select_canonical([e1, e2, e3])
        assert canonical is e2

    def test_ties_broken_by_confidence(self):
        e1 = _capability(source_refs=["url1"], confidence=0.6)
        e2 = _capability(source_refs=["url1"], confidence=0.9)
        canonical = self.dedup._select_canonical([e1, e2])
        assert canonical is e2

    def test_single_entity_returned(self):
        e = _capability()
        canonical = self.dedup._select_canonical([e])
        assert canonical is e

    def test_entity_without_source_refs_loses_to_one_with_refs(self):
        e_no_refs = _capability(source_refs=[])
        e_with_refs = _capability(source_refs=["url1"])
        canonical = self.dedup._select_canonical([e_no_refs, e_with_refs])
        assert canonical is e_with_refs


# ---------------------------------------------------------------------------
# _entity_to_text
# ---------------------------------------------------------------------------

class TestEntityToText:
    def setup_method(self):
        self.dedup = _make_dedup()

    def test_capability_text_contains_name(self):
        cap = _capability(name="Real-Time Ingestion")
        text = self.dedup._entity_to_text(cap)
        assert "Real-Time Ingestion" in text

    def test_capability_text_contains_technical_features(self):
        cap = _capability(features=["Kafka", "CDC", "Schema Registry"])
        text = self.dedup._entity_to_text(cap)
        assert "Kafka" in text
        assert "CDC" in text

    def test_use_case_text_contains_name(self):
        uc = _use_case(name="Budget Forecasting")
        text = self.dedup._entity_to_text(uc)
        assert "Budget Forecasting" in text

    def test_use_case_text_contains_industry(self):
        uc = _use_case(industries=["Manufacturing", "Retail"])
        text = self.dedup._entity_to_text(uc)
        assert "Manufacturing" in text

    def test_persona_text_contains_title(self):
        p = _persona(title="VP of Finance")
        text = self.dedup._entity_to_text(p)
        assert "VP of Finance" in text

    def test_persona_text_contains_department(self):
        p = _persona(department="Engineering")
        text = self.dedup._entity_to_text(p)
        assert "Engineering" in text

    def test_persona_text_contains_pain_points(self):
        p = _persona(pain_points=["Budget constraints", "Slow reporting"])
        text = self.dedup._entity_to_text(p)
        assert "Budget constraints" in text

    def test_value_driver_text_contains_name(self):
        vd = _value_driver(name="Revenue Growth")
        text = self.dedup._entity_to_text(vd)
        assert "Revenue Growth" in text

    def test_value_driver_text_contains_category(self):
        vd = _value_driver()
        text = self.dedup._entity_to_text(vd)
        assert "cost_reduction" in text

    def test_value_driver_text_contains_metrics(self):
        vd = _value_driver(metrics=["FTE savings", "Error rate"])
        text = self.dedup._entity_to_text(vd)
        assert "FTE savings" in text

    def test_feature_text_contains_name(self):
        f = _feature(name="Auto-Reconcile")
        text = self.dedup._entity_to_text(f)
        assert "Auto-Reconcile" in text

    def test_feature_text_contains_status(self):
        f = _feature(status="beta")
        text = self.dedup._entity_to_text(f)
        assert "beta" in text

    def test_feature_text_contains_technical_spec(self):
        f = _feature(spec="Uses ML matching with 98% accuracy")
        text = self.dedup._entity_to_text(f)
        assert "ML matching" in text

    def test_unknown_entity_returns_empty_string(self):
        from pydantic import BaseModel
        class Unknown(BaseModel):
            val: str = "x"
        text = self.dedup._entity_to_text(Unknown())
        assert isinstance(text, str)


# ---------------------------------------------------------------------------
# _merge_into_canonical (via type-specific merge helpers)
# ---------------------------------------------------------------------------

class TestMergeIntoCanonical:
    def setup_method(self):
        self.dedup = _make_dedup()

    # -- confidence -----------------------------------------------------------

    def test_merge_keeps_highest_confidence(self):
        canonical = _capability(confidence=0.6)
        other = _capability(confidence=0.95)
        self.dedup._merge_into_canonical(canonical, [canonical, other])
        assert canonical.confidence == 0.95

    # -- source_refs ----------------------------------------------------------

    def test_merge_unions_source_refs(self):
        canonical = _capability(source_refs=["url1"])
        other = _capability(source_refs=["url2", "url3"])
        self.dedup._merge_into_canonical(canonical, [canonical, other])
        assert set(canonical.source_refs) == {"url1", "url2", "url3"}

    # -- Capability merge -----------------------------------------------------

    def test_capability_merge_unions_technical_features(self):
        cap1 = _capability(features=["Kafka"])
        cap2 = _capability(features=["CDC"])
        self.dedup._merge_capability_fields(cap1, [cap1, cap2])
        assert "Kafka" in cap1.technical_features
        assert "CDC" in cap1.technical_features

    def test_capability_merge_unions_integrations(self):
        cap1 = _capability()
        cap1.integrations = ["Salesforce"]
        cap2 = _capability()
        cap2.integrations = ["HubSpot"]
        self.dedup._merge_capability_fields(cap1, [cap1, cap2])
        assert "Salesforce" in cap1.integrations
        assert "HubSpot" in cap1.integrations

    # -- UseCase merge --------------------------------------------------------

    def test_usecase_merge_unions_industries(self):
        uc1 = _use_case(industries=["Finance"])
        uc2 = _use_case(industries=["Healthcare"])
        self.dedup._merge_usecase_fields(uc1, [uc1, uc2])
        assert "Finance" in uc1.industry_context
        assert "Healthcare" in uc1.industry_context

    def test_usecase_merge_unions_kpis(self):
        uc1 = _use_case()
        uc1.kpis = ["Cycle time"]
        uc2 = _use_case()
        uc2.kpis = ["Error rate"]
        self.dedup._merge_usecase_fields(uc1, [uc1, uc2])
        assert "Cycle time" in uc1.kpis
        assert "Error rate" in uc1.kpis

    def test_usecase_merge_preserves_workflow_step_order(self):
        uc1 = _use_case()
        uc1.workflow_steps = ["Step A", "Step B"]
        uc2 = _use_case()
        uc2.workflow_steps = ["Step C"]
        self.dedup._merge_usecase_fields(uc1, [uc1, uc2])
        assert uc1.workflow_steps[0] == "Step A"
        assert "Step C" in uc1.workflow_steps

    # -- Persona merge --------------------------------------------------------

    def test_persona_merge_unions_pain_points(self):
        p1 = _persona(pain_points=["Slow reporting"])
        p2 = _persona(pain_points=["Budget overruns"])
        self.dedup._merge_persona_fields(p1, [p1, p2])
        assert "Slow reporting" in p1.pain_points
        assert "Budget overruns" in p1.pain_points

    # -- ValueDriver merge ----------------------------------------------------

    def test_valuedriver_merge_unions_metrics(self):
        vd1 = _value_driver(metrics=["FTE savings"])
        vd2 = _value_driver(metrics=["Error reduction"])
        self.dedup._merge_valuedriver_fields(vd1, [vd1, vd2])
        assert "FTE savings" in vd1.metrics
        assert "Error reduction" in vd1.metrics

    # -- Feature merge --------------------------------------------------------

    def test_feature_merge_keeps_longest_technical_spec(self):
        f1 = _feature(spec="Short spec.")
        f2 = _feature(spec="A much longer and more detailed technical specification.")
        self.dedup._merge_feature_fields(f1, [f1, f2])
        assert f1.technical_spec == "A much longer and more detailed technical specification."

    def test_feature_merge_keeps_most_advanced_status(self):
        f_planned = _feature(status="planned")
        f_ga = _feature(status="ga")
        self.dedup._merge_feature_fields(f_planned, [f_planned, f_ga])
        assert f_planned.implementation_status == "ga"

    def test_feature_merge_beta_beats_planned(self):
        f_planned = _feature(status="planned")
        f_beta = _feature(status="beta")
        self.dedup._merge_feature_fields(f_planned, [f_planned, f_beta])
        assert f_planned.implementation_status == "beta"

    def test_feature_merge_ga_beats_beta(self):
        f_beta = _feature(status="beta")
        f_ga = _feature(status="ga")
        self.dedup._merge_feature_fields(f_beta, [f_beta, f_ga])
        assert f_beta.implementation_status == "ga"
