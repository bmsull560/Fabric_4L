"""Prompt templates for entity and relationship extraction.

This package contains text-based prompt templates for LLM extraction.
Templates are loaded by PromptTemplate class and support variable substitution.

Available templates:
- capability_extraction.txt
- usecase_extraction.txt
- persona_extraction.txt
- valuedriver_extraction.txt
- feature_extraction.txt
- relationship_extraction.txt
- operational_signal_extraction.txt (Phase 3)
"""

import os


def load_prompt(filename: str) -> str:
    """Load a prompt template from file.

    Args:
        filename: Name of the prompt file (e.g., "capability_extraction.txt")

    Returns:
        Prompt template content as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompts_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(prompts_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prompt file not found: {filename}")

    with open(filepath, encoding="utf-8") as f:
        return f.read()


__all__ = ["load_prompt"]
