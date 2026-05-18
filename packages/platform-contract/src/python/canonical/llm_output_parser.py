"""Canonical §2.5 boundary for parsing LLM text output into structured dicts.

All agent and extraction code that reads JSON from a raw LLM response must go
through ``parse_llm_json``.  Direct ``json.loads`` on LLM content is a
Contract §2.5 violation.

The parser applies a two-stage strategy:
1. Direct parse — works when the model returns clean JSON.
2. Bracket extraction — finds the first ``{...}`` or ``[...]`` span using a
   depth counter to locate the correct matching close bracket, then retries.
   This handles models that wrap JSON in prose or markdown fences.

On total failure the function returns an empty dict and logs a warning so
callers always receive a dict, never a parse exception.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _find_matching_close(content: str, start: int, open_char: str, close_char: str) -> int:
    """Return the index of the close bracket that matches the open bracket at ``start``.

    Uses a depth counter so stray brackets after the JSON span do not produce
    an incorrect end position (the ``rfind`` approach fails in that case).

    Returns -1 if no matching close bracket is found.
    """
    depth = 0
    for i in range(start, len(content)):
        if content[i] == open_char:
            depth += 1
        elif content[i] == close_char:
            depth -= 1
            if depth == 0:
                return i
    return -1


def parse_llm_json(content: str, *, call_site: str = "") -> dict[str, Any]:
    """Parse a raw LLM response string into a dict.

    Args:
        content: Raw text from the LLM response (or function-call arguments).
        call_site: Optional label for log messages (e.g. ``"intent_classifier"``).

    Returns:
        Parsed dict, or ``{}`` if parsing fails entirely.
    """
    if not content or not content.strip():
        return {}

    # Stage 1: direct parse
    try:
        result = json.loads(content)
        if isinstance(result, dict):
            return result
        # LLM returned a JSON array or scalar — wrap so callers always get a dict
        return {"result": result}
    except json.JSONDecodeError:
        pass

    # Stage 2: bracket extraction — find first { or [ and its matching close
    for open_char, close_char in [('{', '}'), ('[', ']')]:
        start = content.find(open_char)
        if start == -1:
            continue
        end = _find_matching_close(content, start, open_char, close_char)
        if end == -1:
            continue
        try:
            result = json.loads(content[start:end + 1])
            if isinstance(result, dict):
                return result
            return {"result": result}
        except json.JSONDecodeError:
            continue

    tag = f" [{call_site}]" if call_site else ""
    logger.warning("parse_llm_json%s: could not extract JSON from response: %r", tag, content[:200])
    return {}
