import json
import math
from types import SimpleNamespace

import pytest

from layer2_extraction.extraction.llm_extractor import (
    EntityExtractor,
    LLMExtractionError,
    _effective_confidence,
    _logprob_confidence_from_response,
    _parse_tool_arguments,
    _strict_array_tool,
)


def _response_with_logprobs(logprobs: list[float]):
    content = [SimpleNamespace(logprob=v) for v in logprobs]
    return SimpleNamespace(
        choices=[SimpleNamespace(logprobs=SimpleNamespace(content=content))]
    )


def _response_with_tool_args(payload: dict):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(arguments=json.dumps(payload))
                        )
                    ]
                )
            )
        ]
    )


def test_logprob_confidence_from_response_calculates_expected_value():
    response = _response_with_logprobs([-0.2, -0.4])
    expected = math.exp((-0.2 + -0.4) / 2)
    actual = _logprob_confidence_from_response(response)
    assert actual == pytest.approx(expected)


def test_logprob_confidence_from_response_returns_none_without_logprobs():
    response = SimpleNamespace(choices=[SimpleNamespace(logprobs=None)])
    assert _logprob_confidence_from_response(response) is None


def test_effective_confidence_blends_item_and_token_confidence():
    actual = _effective_confidence(0.8, 0.5)
    assert actual == pytest.approx((0.7 * 0.8) + (0.3 * 0.5))


def test_effective_confidence_clamps_out_of_range_values():
    assert _effective_confidence(2.0, None) == 1.0
    assert _effective_confidence(-1.0, 0.5) >= 0.0


def test_parse_tool_arguments_returns_json_payload():
    response = _response_with_tool_args({"capabilities": [{"name": "x"}]})
    parsed = _parse_tool_arguments(response, "extract_capabilities")
    assert parsed["capabilities"][0]["name"] == "x"


def test_parse_tool_arguments_raises_for_missing_tool_call():
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[]))])
    with pytest.raises(LLMExtractionError):
        _parse_tool_arguments(response, "extract_capabilities")


def test_strict_array_tool_enforces_strict_schema_shape():
    tools = _strict_array_tool(
        function_name="extract_capabilities",
        description="Extract capabilities",
        array_field_name="capabilities",
        item_schema={"type": "object"},
    )

    function = tools[0]["function"]
    parameters = function["parameters"]
    assert function["strict"] is True
    assert parameters["required"] == ["capabilities"]
    assert parameters["additionalProperties"] is False


def test_entity_schema_constants_are_strict():
    assert EntityExtractor.USECASE_SCHEMA["additionalProperties"] is False
    assert EntityExtractor.FEATURE_SCHEMA["additionalProperties"] is False
