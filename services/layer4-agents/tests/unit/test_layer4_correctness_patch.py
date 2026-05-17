"""Unit tests for the Layer 4 correctness patch (4 issues).

Groups:
  A — GovernedLLMClient cost-cap enforcement
  B — _execute_validate_claims Layer 5 client lifecycle
  C — _execute_validate_claims MissingTenantContextError degradation
  D — SignalDetectionAgent._detect_signals failure path
"""

from __future__ import annotations

import os
import types
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helpers — minimal stubs for heavy optional deps
# ---------------------------------------------------------------------------

def _stub_module(name: str) -> types.ModuleType:
    m = types.ModuleType(name)
    import sys
    sys.modules.setdefault(name, m)
    return sys.modules[name]


# ---------------------------------------------------------------------------
# Group A — GovernedLLMClient cost-cap enforcement
# ---------------------------------------------------------------------------


class _FakeUsage:
    prompt_tokens = 100
    completion_tokens = 200


class _FakeResponse:
    content = '{"result": "ok"}'
    usage = _FakeUsage()


def _make_client(max_cost: float | None = None, provider_side_effect=None):
    """Build a GovernedLLMClient with a mocked provider and optional cost cap."""
    from value_fabric.layer4.services.governed_llm_client import GovernedLLMClient

    provider = MagicMock()
    if provider_side_effect is not None:
        provider.complete_text = AsyncMock(side_effect=provider_side_effect)
    else:
        provider.complete_text = AsyncMock(return_value=_FakeResponse())

    config: dict[str, Any] = {"llm": {"retry": {"max_attempts": 3, "backoff_seconds": 0}}}
    if max_cost is not None:
        config["llm"]["max_cost_per_call_usd"] = max_cost

    with patch.object(GovernedLLMClient, "_load_runtime_config", return_value=config), \
         patch.object(GovernedLLMClient, "_build_cost_calculator", return_value=None):
        client = GovernedLLMClient(  # type: ignore[call-arg]
            provider=provider,
            provider_name="test",
        )

    return client, provider


class TestCostCapEnforcement:
    """Group A — cost-cap enforcement in GovernedLLMClient."""

    def test_cost_cap_loaded_from_config(self):
        """max_cost_per_call_usd is read from config at init time."""
        client, _ = _make_client(max_cost=0.50)
        assert client._max_cost_per_call_usd == 0.50

    def test_no_cost_cap_when_absent(self):
        """_max_cost_per_call_usd is None when key is absent from config."""
        client, _ = _make_client(max_cost=None)
        assert client._max_cost_per_call_usd is None

    async def test_under_cap_call_reaches_provider(self):
        """A call whose cost is under the cap completes normally."""
        client, provider = _make_client(max_cost=1.00)
        # _calculate_cost returns 0.0 when cost_calc is None — always under cap
        result = await client.call(
            model_task="reasoning",
            messages=[{"role": "user", "content": "hello"}],
        )
        provider.complete_text.assert_called_once()
        assert result.content == _FakeResponse.content

    async def test_over_cap_call_raises(self):
        """A call whose cost exceeds the cap raises _CostCapExceeded."""
        from value_fabric.layer4.services.governed_llm_client import _CostCapExceeded

        client, provider = _make_client(max_cost=0.001)

        with patch.object(client, "_calculate_cost", return_value=0.50):
            with pytest.raises(_CostCapExceeded):
                await client.call(
                    model_task="reasoning",
                    messages=[{"role": "user", "content": "hello"}],
                )

    async def test_over_cap_call_does_not_retry(self):
        """An over-cap call must not trigger a retry — provider called exactly once."""
        from value_fabric.layer4.services.governed_llm_client import _CostCapExceeded

        client, provider = _make_client(max_cost=0.001)

        with patch.object(client, "_calculate_cost", return_value=0.50):
            with pytest.raises(_CostCapExceeded):
                await client.call(
                    model_task="reasoning",
                    messages=[{"role": "user", "content": "hello"}],
                )

        provider.complete_text.assert_called_once()

    async def test_over_cap_emits_single_failure_event(self):
        """An over-cap call emits exactly one llm_call_failed event."""
        from value_fabric.layer4.services.governed_llm_client import _CostCapExceeded

        client, _ = _make_client(max_cost=0.001)
        emitted: list[tuple[str, dict]] = []

        def _capture(event_type: str, metadata: dict) -> None:
            emitted.append((event_type, metadata))

        with patch.object(client, "_emit_raw", side_effect=_capture), \
             patch.object(client, "_calculate_cost", return_value=0.50):
            with pytest.raises(_CostCapExceeded):
                await client.call(
                    model_task="reasoning",
                    messages=[{"role": "user", "content": "hello"}],
                )

        failed_events = [(t, m) for t, m in emitted if t == "llm_call_failed"]
        assert len(failed_events) == 1
        assert failed_events[0][1]["error"] == "cost_cap_exceeded"
        assert failed_events[0][1]["cost_usd"] == 0.50

    async def test_transient_error_is_retried(self):
        """A TIMEOUT error is retried up to max_attempts times."""
        timeout_exc = Exception("connection timeout")
        client, provider = _make_client(
            max_cost=None,
            provider_side_effect=timeout_exc,
        )

        with pytest.raises(Exception, match="timeout"):
            await client.call(
                model_task="reasoning",
                messages=[{"role": "user", "content": "hello"}],
            )

        assert provider.complete_text.call_count == 3  # max_attempts=3


# ---------------------------------------------------------------------------
# Group B — Layer 5 client lifecycle in _execute_validate_claims
# ---------------------------------------------------------------------------


def _make_workflow_state(
    sections: list | None = None,
    tenant_id: str = "tenant-001",
    authenticated_tenant_id: str = "org-001",
):
    """Build a minimal BusinessCaseAgentState for validate_claims tests."""
    state = MagicMock()
    state.metadata = {
        "tenant_id": tenant_id,
        "authenticated_tenant_id": authenticated_tenant_id,
    }
    state.case_input = MagicMock()
    state.case_input.custom_inputs = {"account_name": "Acme Corp"}
    state.input_data = {}
    state.output_data = {
        "generate_narrative": {
            "sections": sections or [{"title": "Exec Summary", "content": "We save 30%."}]
        }
    }
    return state


def _make_bc_workflow():
    """Build a BusinessCaseGeneratorWorkflow with mocked dependencies."""
    from value_fabric.layer4.workflows.business_case import BusinessCaseGeneratorWorkflow

    tool_registry = MagicMock()
    with patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
         patch("value_fabric.layer4.workflows.business_case.get_prompt_registry"):
        wf = BusinessCaseGeneratorWorkflow(tool_registry=tool_registry)
    return wf


class TestL5ClientLifecycle:
    """Group B — Layer5GroundTruthClient constructed once per validate_claims call."""

    async def test_l5_client_constructed_once(self, monkeypatch):
        """Layer5GroundTruthClient constructor is called once regardless of claim count."""
        monkeypatch.setenv("LAYER5_GROUND_TRUTH_URL", "http://l5:8005")
        monkeypatch.setenv("LAYER5_SERVICE_TOKEN", "tok")

        constructor_calls = []

        fake_client = AsyncMock()
        fake_client.close = AsyncMock()

        def _fake_constructor(**kwargs):
            constructor_calls.append(kwargs)
            return fake_client

        fake_validator = MagicMock()
        fake_validator.validate_claim = AsyncMock(return_value={"validated": True, "evidence": []})

        # LLM returns 3 claims
        fake_llm_result = MagicMock()
        fake_llm_result.content = '{"claims": [{"claim_text": "A"}, {"claim_text": "B"}, {"claim_text": "C"}]}'
        fake_llm_result.model = "test-model"
        fake_llm_result.prompt_tokens = 10
        fake_llm_result.completion_tokens = 20

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry") as mock_reg, \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient") as MockLLM, \
             patch("value_fabric.layer4.workflows.business_case.Layer5GroundTruthClient", side_effect=_fake_constructor), \
             patch("value_fabric.layer4.harness.live_l5_validator.LiveL5Validator", return_value=fake_validator) as MockValidator:

            mock_reg.return_value.get.return_value = MagicMock(
                body="sys", model_task="reasoning", temperature=0.2, max_tokens=512,
                render=MagicMock(return_value="user content"),
            )
            MockLLM.return_value.call = AsyncMock(return_value=fake_llm_result)
            MockLLM.return_value._parse_json = MagicMock(
                return_value={"claims": [{"claim_text": "A"}, {"claim_text": "B"}, {"claim_text": "C"}]}
            )

            wf = _make_bc_workflow()
            await wf._execute_validate_claims(state)

        assert len(constructor_calls) == 1, "Layer5GroundTruthClient must be constructed exactly once"

    async def test_l5_client_closed_in_finally(self, monkeypatch):
        """l5_client.close() is called even when a claim raises."""
        monkeypatch.setenv("LAYER5_GROUND_TRUTH_URL", "http://l5:8005")
        monkeypatch.setenv("LAYER5_SERVICE_TOKEN", "tok")

        fake_client = AsyncMock()
        fake_client.close = AsyncMock()

        fake_validator = MagicMock()
        fake_validator.validate_claim = AsyncMock(side_effect=RuntimeError("l5 down"))

        fake_llm_result = MagicMock()
        fake_llm_result.content = '{"claims": [{"claim_text": "A"}]}'
        fake_llm_result.model = "test-model"
        fake_llm_result.prompt_tokens = 10
        fake_llm_result.completion_tokens = 20

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry") as mock_reg, \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient") as MockLLM, \
             patch("value_fabric.layer4.workflows.business_case.Layer5GroundTruthClient", return_value=fake_client), \
             patch("value_fabric.layer4.harness.live_l5_validator.LiveL5Validator", return_value=fake_validator):

            mock_reg.return_value.get.return_value = MagicMock(
                body="sys", model_task="reasoning", temperature=0.2, max_tokens=512,
                render=MagicMock(return_value="user content"),
            )
            MockLLM.return_value.call = AsyncMock(return_value=fake_llm_result)
            MockLLM.return_value._parse_json = MagicMock(
                return_value={"claims": [{"claim_text": "A"}]}
            )

            wf = _make_bc_workflow()
            result = await wf._execute_validate_claims(state)

        # close() must have been called despite the per-claim exception
        fake_client.close.assert_called_once()
        # The claim should be in unverified (exception caught per-claim)
        assert result["payload"]["unverified_count"] >= 1

    async def test_missing_l5_url_returns_unavailable(self, monkeypatch):
        """When LAYER5_GROUND_TRUTH_URL is empty, all claims get l5_status: unavailable."""
        # Set to empty string — the code checks `if not layer5_url`
        monkeypatch.setenv("LAYER5_GROUND_TRUTH_URL", "")
        monkeypatch.delenv("LAYER5_SERVICE_TOKEN", raising=False)

        fake_llm_result = MagicMock()
        fake_llm_result.model = "test-model"
        fake_llm_result.prompt_tokens = 10
        fake_llm_result.completion_tokens = 20

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry") as mock_reg, \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient") as MockLLM, \
             patch("value_fabric.layer4.workflows.business_case.Layer5GroundTruthClient") as MockL5:

            mock_reg.return_value.get.return_value = MagicMock(
                body="sys", model_task="reasoning", temperature=0.2, max_tokens=512,
                render=MagicMock(return_value="user content"),
            )
            MockLLM.return_value.call = AsyncMock(return_value=fake_llm_result)
            MockLLM.return_value._parse_json = MagicMock(
                return_value={"claims": [{"claim_text": "A"}, {"claim_text": "B"}]}
            )

            wf = _make_bc_workflow()
            result = await wf._execute_validate_claims(state)

        # Layer5GroundTruthClient must not be constructed
        MockL5.assert_not_called()
        # All claims must be unverified with unavailable status
        unverified = result["payload"]["unverified_claims"]
        assert all(c["l5_status"] == "unavailable" for c in unverified)


# ---------------------------------------------------------------------------
# Group C — MissingTenantContextError degradation in _execute_validate_claims
# ---------------------------------------------------------------------------


class TestMissingTenantDegradation:
    """Group C — MissingTenantContextError returns degraded result, not exception."""

    async def test_missing_tenant_returns_degraded(self):
        """MissingTenantContextError is caught and returns a degraded dict."""
        from value_fabric.layer4.workflows.business_case import MissingTenantContextError

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry"), \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient"):

            wf = _make_bc_workflow()
            with patch.object(wf, "_resolve_organization_id", side_effect=MissingTenantContextError("no tenant")):
                result = await wf._execute_validate_claims(state)

        # Must return (not raise) — result is a TypedDictModel or dict
        assert result is not None
        assert hasattr(result, "get") or isinstance(result, dict)

    async def test_missing_tenant_degraded_reason(self):
        """degraded_reason is exactly 'missing_tenant_context'."""
        from value_fabric.layer4.workflows.business_case import MissingTenantContextError

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry"), \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient"):

            wf = _make_bc_workflow()
            with patch.object(wf, "_resolve_organization_id", side_effect=MissingTenantContextError("no tenant")):
                result = await wf._execute_validate_claims(state)

        assert result.get("degraded_reason") == "missing_tenant_context"

    async def test_missing_tenant_no_llm_call(self):
        """LLM provider is not called when MissingTenantContextError is raised."""
        from value_fabric.layer4.workflows.business_case import MissingTenantContextError

        state = _make_workflow_state()
        mock_llm_instance = MagicMock()
        mock_llm_instance.call = AsyncMock()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry"), \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient", return_value=mock_llm_instance):

            wf = _make_bc_workflow()
            with patch.object(wf, "_resolve_organization_id", side_effect=MissingTenantContextError("no tenant")):
                await wf._execute_validate_claims(state)

        mock_llm_instance.call.assert_not_called()

    async def test_missing_tenant_human_review_required(self):
        """human_review_required is True on missing-tenant degraded result."""
        from value_fabric.layer4.workflows.business_case import MissingTenantContextError

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry"), \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient"):

            wf = _make_bc_workflow()
            with patch.object(wf, "_resolve_organization_id", side_effect=MissingTenantContextError("no tenant")):
                result = await wf._execute_validate_claims(state)

        assert result.get("human_review_required") is True

    async def test_missing_tenant_not_customer_facing(self):
        """customer_facing_allowed is False on missing-tenant degraded result."""
        from value_fabric.layer4.workflows.business_case import MissingTenantContextError

        state = _make_workflow_state()

        with patch("value_fabric.layer4.workflows.business_case.get_prompt_registry"), \
             patch("value_fabric.layer4.workflows.business_case.get_llm_provider"), \
             patch("value_fabric.layer4.workflows.business_case.GovernedLLMClient"):

            wf = _make_bc_workflow()
            with patch.object(wf, "_resolve_organization_id", side_effect=MissingTenantContextError("no tenant")):
                result = await wf._execute_validate_claims(state)

        assert result.get("customer_facing_allowed") is False


# ---------------------------------------------------------------------------
# Group D — SignalDetectionAgent._detect_signals failure path
# ---------------------------------------------------------------------------


def _make_signal_agent():
    """Build a SignalDetectionAgent with minimal config."""
    from value_fabric.layer4.agents.signal_detection import SignalDetectionAgent

    agent = SignalDetectionAgent.__new__(SignalDetectionAgent)
    agent.config = {}
    agent.layer2_client = None
    agent.layer3_client = None
    agent.stream_callback = None
    agent.max_signals = 3
    agent.evidence_match_limit = 5
    # Provide a minimal _id_gen stub
    id_gen = MagicMock()
    id_gen.generate = MagicMock(return_value="abc123def456")
    agent._id_gen = id_gen
    return agent


def _make_ctx(tenant_id: str = "tenant-001", trace_id: str = "trace-001"):
    ctx = MagicMock()
    ctx.tenant_id = tenant_id
    ctx.trace_id = trace_id
    return ctx


class TestSignalDetectionFailurePath:
    """Group D — _detect_signals failure path and llm_output contract."""

    async def test_success_path_includes_llm_output(self):
        """Success path return dict contains llm_output key populated from _execute_llm_layer."""
        agent = _make_signal_agent()
        ctx = _make_ctx()

        fake_llm_output = {"classified": [], "hypotheses": [], "narrative": "ok"}

        # Use a MagicMock PainSignal to avoid model validation on raw fixture data
        fake_signal = MagicMock()
        fake_signal.id = "sig_abc123"
        fake_signal.confidence_score = 0.8
        fake_signal.evidence_matches = []
        fake_signal.impact_value = None
        fake_signal.model_dump = MagicMock(return_value={"id": "sig_abc123"})

        with patch.object(agent, "_extract_signals_from_layer2", return_value={"signals": [{"name": "s"}], "duration_ms": 10}), \
             patch.object(agent, "_create_pain_signal", return_value=fake_signal), \
             patch.object(agent, "_persist_signal", return_value=None), \
             patch.object(agent, "_execute_llm_layer", return_value=fake_llm_output):

            result = await agent._detect_signals(
                parameters={"prospect_data": {"account_id": "acct-1"}, "options": {"include_evidence": False, "quantify_impact": False}},
                ctx=ctx,
            )

        # llm_output must be present and match what _execute_llm_layer returned
        llm_out = result.get("llm_output") if hasattr(result, "get") else result["llm_output"]
        assert llm_out == fake_llm_output

    async def test_safe_failure_returns_degraded(self):
        """A generic RuntimeError in the pipeline returns a degraded result, not re-raises."""
        agent = _make_signal_agent()
        ctx = _make_ctx()

        with patch.object(agent, "_extract_signals_from_layer2", side_effect=RuntimeError("network down")):
            result = await agent._detect_signals(
                parameters={"prospect_data": {"account_id": "acct-1"}, "options": {}},
                ctx=ctx,
            )

        # Must return (not raise) — result is a TypedDictModel or dict
        message = result.get("message") if hasattr(result, "get") else result["message"]
        assert "degraded" in message.lower()

    async def test_governance_failure_reraises(self):
        """A ValueError (governance/programming error) propagates out of _detect_signals."""
        agent = _make_signal_agent()
        ctx = _make_ctx()

        with patch.object(agent, "_extract_signals_from_layer2", side_effect=ValueError("invalid state")):
            with pytest.raises(ValueError, match="invalid state"):
                await agent._detect_signals(
                    parameters={"prospect_data": {"account_id": "acct-1"}, "options": {}},
                    ctx=ctx,
                )

    async def test_stream_event_emitted_on_safe_failure(self):
        """SignalFailedEvent is emitted before returning the degraded result."""
        agent = _make_signal_agent()
        ctx = _make_ctx()

        # stream_callback is set on the instance (not from parameters in _detect_signals)
        stream_calls: list = []

        async def _fake_stream(event_json: str) -> None:
            stream_calls.append(event_json)

        agent.stream_callback = _fake_stream

        emit_calls: list = []

        async def _fake_emit(event: Any) -> None:
            emit_calls.append(event)

        with patch.object(agent, "_extract_signals_from_layer2", side_effect=RuntimeError("timeout")), \
             patch.object(agent, "_emit_event", side_effect=_fake_emit):

            result = await agent._detect_signals(
                parameters={"prospect_data": {"account_id": "acct-1"}, "options": {}},
                ctx=ctx,
            )

        # The degraded result must have been returned (not raised)
        assert result is not None
        # _emit_event must have been called (SignalFailedEvent was passed to it)
        assert len(emit_calls) >= 1
