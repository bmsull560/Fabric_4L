"""Tests for GATE Phase 2: ABOM, PolicyEngine, Invariants, ToolGateway.

Covers:
- ABOM model loading and validation
- ABOM manifest hash determinism
- PolicyEngineClient local fallback (OPA unavailable)
- High-privilege deny-all when OPA is down
- InvariantEvaluator tool call limits and budget caps
- ToolGateway end-to-end pipeline (allow, deny, invariant block)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import jsonschema
import pytest

from shared.governance.abom import (
    ABOMInvariants,
    AgentBillOfMaterials,
    clear_abom_cache,
    load_abom,
)
from shared.governance.invariants import InvariantEvaluator
from shared.governance.policy_engine import PolicyDecision, PolicyEngineClient
from shared.governance.tool_gateway import (
    InvariantViolation,
    ToolGateway,
    ToolGatewayDenied,
)

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "packages" / "platform-contract" / "schemas" / "gate"


def _make_abom(**overrides) -> AgentBillOfMaterials:
    """Create a test ABOM with sensible defaults."""
    defaults = {
        "agent_type": "TestAgent",
        "agent_id": "TestAgent-abcd1234",
        "privilege_tier": "standard",
        "allowed_tools": ["tool_a", "tool_b", "tool_c"],
        "denied_tools": [],
        "invariants": ABOMInvariants(
            max_tool_calls_per_run=5,
            budget_limit_usd=10.0,
        ),
    }
    defaults.update(overrides)
    return AgentBillOfMaterials(**defaults)


def _make_mock_registry() -> MagicMock:
    """Create a mock ToolRegistry."""
    registry = MagicMock()
    registry.execute = AsyncMock(return_value={"status": "ok"})
    return registry


# ═══════════════════════════════════════════════════════════════════════════
# ABOM Model Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestABOMModel:
    """AgentBillOfMaterials model tests."""

    def test_is_tool_allowed(self) -> None:
        abom = _make_abom()
        assert abom.is_tool_allowed("tool_a") is True
        assert abom.is_tool_allowed("unknown_tool") is False

    def test_denied_tools_override_allowed(self) -> None:
        abom = _make_abom(
            allowed_tools=["tool_a", "tool_b"],
            denied_tools=["tool_a"],
        )
        assert abom.is_tool_allowed("tool_a") is False
        assert abom.is_tool_allowed("tool_b") is True

    def test_manifest_hash_determinism(self) -> None:
        abom1 = _make_abom()
        abom2 = _make_abom()
        assert abom1.manifest_hash() == abom2.manifest_hash()

    def test_manifest_hash_changes_with_tools(self) -> None:
        abom1 = _make_abom(allowed_tools=["tool_a"])
        abom2 = _make_abom(allowed_tools=["tool_a", "tool_b"])
        assert abom1.manifest_hash() != abom2.manifest_hash()

    def test_load_abom_from_file(self, tmp_path: Path) -> None:
        clear_abom_cache()
        manifest = {
            "schema_version": "1.0",
            "agent_type": "FileAgent",
            "agent_id": "FileAgent-12345678",
            "privilege_tier": "standard",
            "allowed_tools": ["tool_x"],
            "invariants": {"max_tool_calls_per_run": 10},
        }
        path = tmp_path / "test.abom.json"
        path.write_text(json.dumps(manifest))
        abom = load_abom(path)
        assert abom.agent_type == "FileAgent"
        assert abom.is_tool_allowed("tool_x")

    def test_abom_conforms_to_schema(self) -> None:
        schema = json.loads(
            (SCHEMA_DIR / "abom.schema.json").read_text()
        )
        abom = _make_abom()
        payload = json.loads(abom.model_dump_json())
        jsonschema.Draft202012Validator(schema).validate(payload)


# ═══════════════════════════════════════════════════════════════════════════
# PolicyEngineClient Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPolicyEngineClient:
    """PolicyEngineClient local fallback tests."""

    @pytest.mark.asyncio
    async def test_local_fallback_allows_listed_tool(self) -> None:
        client = PolicyEngineClient(opa_url="http://nonexistent:9999", timeout=1)
        abom = _make_abom()
        decision = await client.evaluate(abom, "tool_a", {})
        assert decision.allowed is True

    @pytest.mark.asyncio
    async def test_local_fallback_denies_unlisted_tool(self) -> None:
        client = PolicyEngineClient(opa_url="http://nonexistent:9999", timeout=1)
        abom = _make_abom()
        decision = await client.evaluate(abom, "unknown_tool", {})
        assert decision.allowed is False

    @pytest.mark.asyncio
    async def test_local_fallback_denies_denied_tool(self) -> None:
        client = PolicyEngineClient(opa_url="http://nonexistent:9999", timeout=1)
        abom = _make_abom(denied_tools=["tool_a"])
        decision = await client.evaluate(abom, "tool_a", {})
        assert decision.allowed is False

    @pytest.mark.asyncio
    async def test_high_privilege_deny_all_when_opa_down(self) -> None:
        """CRITICAL: high_privilege agents must be denied when OPA is unavailable."""
        client = PolicyEngineClient(opa_url="http://nonexistent:9999", timeout=1)
        abom = _make_abom(privilege_tier="high_privilege")
        decision = await client.evaluate(abom, "tool_a", {})
        assert decision.allowed is False
        assert "deny-all" in decision.reason


# ═══════════════════════════════════════════════════════════════════════════
# InvariantEvaluator Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestInvariantEvaluator:
    """InvariantEvaluator tests."""

    def test_allows_within_limits(self) -> None:
        abom = _make_abom()
        evaluator = InvariantEvaluator(abom)
        result = evaluator.check_pre_invocation("tool_a")
        assert result.passed is True

    def test_blocks_over_call_limit(self) -> None:
        abom = _make_abom()
        evaluator = InvariantEvaluator(abom)
        for _ in range(5):
            evaluator.record_invocation("tool_a")
        result = evaluator.check_pre_invocation("tool_a")
        assert result.passed is False
        assert any("limit exceeded" in v for v in result.violations)

    def test_blocks_over_budget(self) -> None:
        abom = _make_abom()
        evaluator = InvariantEvaluator(abom)
        result = evaluator.check_pre_invocation("tool_a", estimated_cost_usd=15.0)
        assert result.passed is False
        assert any("Budget" in v for v in result.violations)

    def test_warns_near_budget(self) -> None:
        abom = _make_abom()
        evaluator = InvariantEvaluator(abom)
        result = evaluator.check_pre_invocation("tool_a", estimated_cost_usd=9.0)
        assert result.passed is True
        assert len(result.warnings) > 0

    def test_reset_clears_state(self) -> None:
        abom = _make_abom()
        evaluator = InvariantEvaluator(abom)
        evaluator.record_invocation("tool_a", cost_usd=5.0)
        evaluator.reset()
        assert evaluator.tool_call_count == 0
        assert evaluator.budget_used_usd == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# ToolGateway Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestToolGateway:
    """ToolGateway end-to-end pipeline tests."""

    @pytest.mark.asyncio
    async def test_allows_valid_invocation(self) -> None:
        registry = _make_mock_registry()
        abom = _make_abom()
        gw = ToolGateway(registry=registry, abom=abom)
        result = await gw.execute("tool_a", {"param": "value"})
        assert result == {"status": "ok"}
        registry.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_denies_unlisted_tool(self) -> None:
        registry = _make_mock_registry()
        abom = _make_abom()
        gw = ToolGateway(registry=registry, abom=abom)
        with pytest.raises(ToolGatewayDenied, match="ABOM denies"):
            await gw.execute("forbidden_tool", {})
        registry.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_denies_denied_tool(self) -> None:
        registry = _make_mock_registry()
        abom = _make_abom(denied_tools=["tool_a"])
        gw = ToolGateway(registry=registry, abom=abom)
        with pytest.raises(ToolGatewayDenied, match="ABOM denies"):
            await gw.execute("tool_a", {})

    @pytest.mark.asyncio
    async def test_invariant_violation_blocks(self) -> None:
        registry = _make_mock_registry()
        abom = _make_abom()
        gw = ToolGateway(registry=registry, abom=abom)
        # Exhaust call limit
        for _ in range(5):
            await gw.execute("tool_a", {})
        with pytest.raises(InvariantViolation, match="limit exceeded"):
            await gw.execute("tool_a", {})

    @pytest.mark.asyncio
    async def test_invocation_log_populated(self) -> None:
        registry = _make_mock_registry()
        abom = _make_abom()
        gw = ToolGateway(registry=registry, abom=abom)
        await gw.execute("tool_a", {"x": 1})
        assert len(gw.invocation_log) == 1
        assert gw.invocation_log[0]["tool_name"] == "tool_a"

    @pytest.mark.asyncio
    async def test_reset_clears_state(self) -> None:
        registry = _make_mock_registry()
        abom = _make_abom()
        gw = ToolGateway(registry=registry, abom=abom)
        await gw.execute("tool_a", {})
        gw.reset_for_new_run()
        assert len(gw.invocation_log) == 0
        assert gw.invariant_evaluator.tool_call_count == 0

    @pytest.mark.asyncio
    async def test_high_privilege_denied_when_opa_down(self) -> None:
        """High-privilege agents must be denied when OPA is unavailable."""
        registry = _make_mock_registry()
        abom = _make_abom(privilege_tier="high_privilege")
        policy_client = PolicyEngineClient(opa_url="http://nonexistent:9999", timeout=1)
        gw = ToolGateway(registry=registry, abom=abom, policy_client=policy_client)
        with pytest.raises(ToolGatewayDenied, match="deny-all"):
            await gw.execute("tool_a", {})
