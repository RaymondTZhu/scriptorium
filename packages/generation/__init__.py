"""Prompt-to-text generation interfaces for Scriptorium."""

from packages.generation.text_prompt import (
    GeneratedTextResult,
    generate_text_from_prompt,
    select_text_for_rendering,
)

__all__ = [
    "GeneratedTextResult",
    "generate_text_from_prompt",
    "select_text_for_rendering",
]
