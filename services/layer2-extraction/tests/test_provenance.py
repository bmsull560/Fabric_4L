"""Tests for provenance tracking (layer2-extraction/src/.../output/provenance.py).

Covers:
- SourceDocument creation
- LLMCall creation and cost calculation via create_llm_call_record()
- ExtractionStep.duration_ms property
- ExtractionActivity: add_step, complete, fail, total_duration_ms, total_llm_calls, total_cost_usd
- ExtractionActivity.get_provenance_chain() – all fields present and correct
- ProvenanceTracker: start_activity, get_activity, get_provenance_for_entity, get_provenance_for_output
- get_provenance_tracker() singleton
"""

import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Direct module import (avoids pulling numpy via the package __init__.py chain)
# ---------------------------------------------------------------------------

_provenance_path = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "layer2_extraction"
    / "output"
    / "provenance.py"
)
_spec = importlib.util.spec_from_file_location("provenance", _provenance_path)
_prov_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prov_mod)

SourceDocument = _prov_mod.SourceDocument
LLMCall = _prov_mod.LLMCall
ExtractionStep = _prov_mod.ExtractionStep
ExtractionActivity = _prov_mod.ExtractionActivity
ExtractionActivityStatus = _prov_mod.ExtractionActivityStatus
ProvenanceTracker = _prov_mod.ProvenanceTracker
get_provenance_tracker = _prov_mod.get_provenance_tracker
create_llm_call_record = _prov_mod.create_llm_call_record


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source_doc(url: str = "https://example.com/doc") -> SourceDocument:
    return SourceDocument(url=url, content_hash="abc123", content_type="product_page")


def _make_llm_call(tokens_in: int = 1000, tokens_out: int = 500) -> LLMCall:
    return LLMCall(
        call_id="call-1",
        model="gpt-4o",
        prompt_hash="ph1",
        prompt_version="v1",
        temperature=0.0,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=0.01,
        duration_ms=300,
    )


def _make_step(name: str = "chunking", entities: int = 5) -> ExtractionStep:
    now = datetime.now(UTC)
    return ExtractionStep(
        step_name=name,
        started_at=now,
        completed_at=now + timedelta(milliseconds=200),
        entities_extracted=entities,
    )


def _make_activity(activity_id: str = "act-1") -> ExtractionActivity:
    return ExtractionActivity(
        activity_id=activity_id,
        status=ExtractionActivityStatus.RUNNING,
        source_document=_make_source_doc(),
    )


# ---------------------------------------------------------------------------
# SourceDocument
# ---------------------------------------------------------------------------

class TestSourceDocument:
    def test_required_fields(self):
        doc = _make_source_doc()
        assert doc.url == "https://example.com/doc"
        assert doc.content_hash == "abc123"

    def test_defaults(self):
        doc = SourceDocument(url="https://x.com", content_hash="h")
        assert doc.size_bytes == 0
        assert doc.http_status == 200
        assert doc.content_type is None

    def test_fetched_at_default_is_datetime(self):
        doc = SourceDocument(url="https://x.com", content_hash="h")
        assert isinstance(doc.fetched_at, datetime)


# ---------------------------------------------------------------------------
# LLMCall
# ---------------------------------------------------------------------------

class TestLLMCall:
    def test_fields_accessible(self):
        call = _make_llm_call()
        assert call.call_id == "call-1"
        assert call.model == "gpt-4o"
        assert call.tokens_in == 1000
        assert call.cost_usd == 0.01

    def test_timestamp_is_datetime(self):
        call = _make_llm_call()
        assert isinstance(call.timestamp, datetime)


# ---------------------------------------------------------------------------
# ExtractionStep
# ---------------------------------------------------------------------------

class TestExtractionStep:
    def test_duration_ms_when_completed(self):
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 0, 0, 1)  # +1 second
        step = ExtractionStep(
            step_name="test", started_at=start, completed_at=end, entities_extracted=0
        )
        assert step.duration_ms == 1000

    def test_duration_ms_none_when_not_completed(self):
        step = ExtractionStep(step_name="test", started_at=datetime.now(UTC))
        assert step.duration_ms is None

    def test_llm_calls_list_default_empty(self):
        step = ExtractionStep(step_name="test", started_at=datetime.now(UTC))
        assert step.llm_calls == []

    def test_errors_list_default_empty(self):
        step = ExtractionStep(step_name="test", started_at=datetime.now(UTC))
        assert step.errors == []


# ---------------------------------------------------------------------------
# ExtractionActivity
# ---------------------------------------------------------------------------

class TestExtractionActivity:
    def test_initial_status_running(self):
        act = _make_activity()
        assert act.status == ExtractionActivityStatus.RUNNING

    def test_add_step_appends(self):
        act = _make_activity()
        step = _make_step()
        act.add_step(step)
        assert len(act.steps) == 1
        assert act.steps[0] is step

    def test_complete_sets_status_and_timestamp(self):
        act = _make_activity()
        act.complete()
        assert act.status == ExtractionActivityStatus.COMPLETED
        assert act.completed_at is not None

    def test_complete_sets_rdf_path(self):
        act = _make_activity()
        act.complete("/output/rdf.ttl")
        assert act.rdf_output_path == "/output/rdf.ttl"

    def test_fail_sets_status_and_timestamp(self):
        act = _make_activity()
        act.fail("Unexpected error")
        assert act.status == ExtractionActivityStatus.FAILED
        assert act.completed_at is not None

    def test_fail_appends_error_to_last_step(self):
        act = _make_activity()
        step = ExtractionStep(step_name="extraction", started_at=datetime.now(UTC))
        act.add_step(step)
        act.fail("Processing error")
        assert "Processing error" in act.steps[-1].errors

    def test_total_duration_ms_when_completed(self):
        act = _make_activity()
        act.started_at = datetime(2024, 1, 1, 0, 0, 0)
        act.completed_at = datetime(2024, 1, 1, 0, 0, 2)
        act.status = ExtractionActivityStatus.COMPLETED
        assert act.total_duration_ms == 2000

    def test_total_duration_ms_none_when_not_completed(self):
        act = _make_activity()
        assert act.total_duration_ms is None

    def test_total_llm_calls_counts_all_steps(self):
        act = _make_activity()
        step1 = _make_step()
        step1.llm_calls = [_make_llm_call(), _make_llm_call()]
        step2 = _make_step()
        step2.llm_calls = [_make_llm_call()]
        act.add_step(step1)
        act.add_step(step2)
        assert act.total_llm_calls == 3

    def test_total_cost_usd_sums_all_calls(self):
        act = _make_activity()
        step = _make_step()
        step.llm_calls = [
            LLMCall("c1", "gpt-4o", "ph", "v1", 0, 100, 50, 0.005, 100),
            LLMCall("c2", "gpt-4o", "ph", "v1", 0, 200, 100, 0.010, 200),
        ]
        act.add_step(step)
        assert abs(act.total_cost_usd - 0.015) < 1e-9

    def test_total_llm_calls_zero_with_no_steps(self):
        act = _make_activity()
        assert act.total_llm_calls == 0

    def test_total_cost_usd_zero_with_no_steps(self):
        act = _make_activity()
        assert act.total_cost_usd == 0.0


# ---------------------------------------------------------------------------
# ExtractionActivity.get_provenance_chain()
# ---------------------------------------------------------------------------

class TestGetProvenanceChain:
    def _completed_activity(self) -> ExtractionActivity:
        act = _make_activity("prov-1")
        step = _make_step("entity_extraction", entities=10)
        step.llm_calls = [_make_llm_call(tokens_in=500, tokens_out=200)]
        act.add_step(step)
        act.output_entities = ["ent-1", "ent-2"]
        act.output_relationships = ["rel-1"]
        act.complete("/path/to/output.ttl")
        return act

    def test_chain_contains_activity_id(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["activity_id"] == "prov-1"

    def test_chain_status_is_completed(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["status"] == "completed"

    def test_chain_source_url(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["source"]["url"] == "https://example.com/doc"

    def test_chain_source_content_hash(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["source"]["content_hash"] == "abc123"

    def test_chain_extraction_total_llm_calls(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["extraction"]["total_llm_calls"] == 1

    def test_chain_output_entity_count(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["output"]["entity_count"] == 2

    def test_chain_output_relationship_count(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["output"]["relationship_count"] == 1

    def test_chain_output_rdf_path(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["output"]["rdf_output_path"] == "/path/to/output.ttl"

    def test_chain_steps_list(self):
        chain = self._completed_activity().get_provenance_chain()
        assert len(chain["steps"]) == 1
        assert chain["steps"][0]["step_name"] == "entity_extraction"

    def test_chain_step_entities_extracted(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["steps"][0]["entities_extracted"] == 10

    def test_chain_step_llm_calls_present(self):
        chain = self._completed_activity().get_provenance_chain()
        assert len(chain["steps"][0]["llm_calls"]) == 1

    def test_chain_extraction_completed_at_not_none(self):
        chain = self._completed_activity().get_provenance_chain()
        assert chain["extraction"]["completed_at"] is not None

    def test_chain_extraction_completed_at_none_when_running(self):
        act = _make_activity()
        chain = act.get_provenance_chain()
        assert chain["extraction"]["completed_at"] is None


# ---------------------------------------------------------------------------
# ProvenanceTracker
# ---------------------------------------------------------------------------

class TestProvenanceTracker:
    def setup_method(self):
        self.tracker = ProvenanceTracker()

    def test_start_activity_returns_activity(self):
        act = self.tracker.start_activity("job-1", "https://x.com", "hash1")
        assert isinstance(act, ExtractionActivity)
        assert act.activity_id == "job-1"

    def test_start_activity_status_running(self):
        act = self.tracker.start_activity("job-1", "https://x.com", "hash1")
        assert act.status == ExtractionActivityStatus.RUNNING

    def test_start_activity_sets_content_type(self):
        act = self.tracker.start_activity("job-2", "https://x.com", "hash2", "blog_post")
        assert act.source_document.content_type == "blog_post"

    def test_get_activity_returns_started_activity(self):
        self.tracker.start_activity("job-3", "https://x.com", "hash3")
        act = self.tracker.get_activity("job-3")
        assert act is not None
        assert act.activity_id == "job-3"

    def test_get_activity_returns_none_for_unknown(self):
        assert self.tracker.get_activity("nonexistent") is None

    def test_get_provenance_for_entity_found(self):
        act = self.tracker.start_activity("job-4", "https://x.com", "hash4")
        act.output_entities = ["entity-abc"]
        act.complete()
        result = self.tracker.get_provenance_for_entity("entity-abc")
        assert result is not None
        assert result["entity_id"] == "entity-abc"

    def test_get_provenance_for_entity_not_found(self):
        result = self.tracker.get_provenance_for_entity("missing-entity")
        assert result is None

    def test_get_provenance_for_output_found(self):
        act = self.tracker.start_activity("job-5", "https://x.com", "hash5")
        act.complete("/output/test.ttl")
        result = self.tracker.get_provenance_for_output("/output/test.ttl")
        assert result is not None

    def test_get_provenance_for_output_not_found(self):
        result = self.tracker.get_provenance_for_output("/nonexistent.ttl")
        assert result is None

    def test_multiple_activities_tracked(self):
        self.tracker.start_activity("job-a", "https://a.com", "ha")
        self.tracker.start_activity("job-b", "https://b.com", "hb")
        assert self.tracker.get_activity("job-a") is not None
        assert self.tracker.get_activity("job-b") is not None


# ---------------------------------------------------------------------------
# get_provenance_tracker() singleton
# ---------------------------------------------------------------------------

class TestGetProvenanceTracker:
    def test_returns_provenance_tracker_instance(self):
        _prov_mod._provenance_tracker = None
        tracker = get_provenance_tracker()
        assert isinstance(tracker, ProvenanceTracker)

    def test_returns_same_instance_on_repeated_calls(self):
        _prov_mod._provenance_tracker = None
        t1 = get_provenance_tracker()
        t2 = get_provenance_tracker()
        assert t1 is t2


# ---------------------------------------------------------------------------
# create_llm_call_record()
# ---------------------------------------------------------------------------

class TestCreateLLMCallRecord:
    def test_returns_llm_call(self):
        record = create_llm_call_record(
            call_id="c1",
            model="gpt-4o",
            prompt_hash="ph",
            prompt_version="v1.0",
            temperature=0.0,
            tokens_in=1000,
            tokens_out=500,
            duration_ms=350,
        )
        assert isinstance(record, LLMCall)

    def test_cost_calculated_for_gpt4o(self):
        record = create_llm_call_record(
            call_id="c2",
            model="gpt-4o",
            prompt_hash="ph",
            prompt_version="v1",
            temperature=0,
            tokens_in=1_000_000,
            tokens_out=0,
            duration_ms=100,
        )
        # 1M input tokens at $2.50/1M = $2.50
        assert abs(record.cost_usd - 2.50) < 0.01

    def test_cost_calculated_for_gpt4o_mini(self):
        record = create_llm_call_record(
            call_id="c3",
            model="gpt-4o-mini",
            prompt_hash="ph",
            prompt_version="v1",
            temperature=0,
            tokens_in=0,
            tokens_out=1_000_000,
            duration_ms=100,
        )
        # 1M output tokens at $0.60/1M = $0.60
        assert abs(record.cost_usd - 0.60) < 0.01

    def test_cost_uses_default_rates_for_unknown_model(self):
        record = create_llm_call_record(
            call_id="c4",
            model="unknown-model",
            prompt_hash="ph",
            prompt_version="v1",
            temperature=0,
            tokens_in=1_000_000,
            tokens_out=0,
            duration_ms=100,
        )
        # Unknown model: $5.00/1M input
        assert abs(record.cost_usd - 5.00) < 0.01

    def test_all_fields_set(self):
        record = create_llm_call_record(
            call_id="c5",
            model="claude-3-5-sonnet",
            prompt_hash="hash123",
            prompt_version="abc",
            temperature=0.5,
            tokens_in=100,
            tokens_out=50,
            duration_ms=200,
        )
        assert record.call_id == "c5"
        assert record.model == "claude-3-5-sonnet"
        assert record.temperature == 0.5
        assert record.tokens_in == 100
        assert record.tokens_out == 50
        assert record.duration_ms == 200
