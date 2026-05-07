from agent_contracts import (
    SEMANTIC_CONTRACT_VERSION,
    ValidationMode,
    build_agent_output_envelope,
    validate_agent_output,
    validate_tool_invocation,
)


def test_agent_output_envelope_builder_normalizes_required_semantic_metadata():
    envelope = build_agent_output_envelope(
        agent_type="ConversationAgent",
        output={"answer": "Phase 2 semantic metadata is present."},
        tenant_id="tenant-123",
        trace_id="trace-123",
        workflow_id="workflow-123",
        prompt_id="conversation-system-prompts",
        prompt_version="1.0.0",
        confidence=0.91,
        evidence=[{"source": "agent-registry"}],
    )

    result = validate_agent_output(envelope)

    assert result.valid is True
    assert result.mode == ValidationMode.WARN
    assert result.violations == []
    assert result.normalized is not None
    assert result.normalized["agent_type"] == "ConversationAgent"
    assert result.normalized["provenance"]["tenant_id"] == "tenant-123"
    assert result.normalized["provenance"]["trace_id"] == "trace-123"
    assert result.normalized["contract_versions"]["semantic_contract"] == SEMANTIC_CONTRACT_VERSION
    assert result.normalized["prompt"]["prompt_id"] == "conversation-system-prompts"


def test_agent_output_validation_reports_blocking_errors_only_in_strict_mode():
    payload = {
        "agent_type": "ConversationAgent",
        "output": {"answer": "missing provenance"},
    }

    warning_result = validate_agent_output(payload, mode="warn")
    strict_result = validate_agent_output(payload, mode="strict")

    assert warning_result.valid is False
    assert warning_result.blocking is False
    assert strict_result.valid is False
    assert strict_result.blocking is True
    assert any(violation.path == "provenance" for violation in strict_result.violations)


def test_tool_invocation_validation_requires_error_envelope_for_failures():
    payload = {
        "tool_name": "platform-tools.search",
        "tool_version": "1.0.0",
        "caller_agent_type": "ConversationAgent",
        "success": False,
        "provenance": {"tenant_id": "tenant-123", "trace_id": "trace-123"},
    }

    result = validate_tool_invocation(payload, mode="strict")

    assert result.valid is False
    assert result.blocking is True
    assert any("failed tool invocations" in violation.message for violation in result.violations)
