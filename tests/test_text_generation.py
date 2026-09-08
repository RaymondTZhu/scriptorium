"""Tests for deterministic prompt-to-text selection."""

import pytest

from packages.generation import generate_text_from_prompt, select_text_for_rendering


def test_local_prompt_generation_is_deterministic() -> None:
    """The local provider should return identical text for identical prompts."""
    prompt = "write a short thank you note to my professor"

    first = generate_text_from_prompt(prompt)
    second = generate_text_from_prompt(prompt)

    assert first == second
    assert first.generated_text == "Thank you for your guidance and support."
    assert first.provider == "local"
    assert first.model is None
    assert first.used_fallback is False


def test_direct_text_selection_preserves_text() -> None:
    """The pipeline selection layer should keep direct text behavior working."""
    result = select_text_for_rendering(text="Hello, World!", prompt=None)

    assert result.generated_text == "Hello, World!"
    assert result.provider == "direct"
    assert result.prompt == ""


def test_prompt_selection_returns_renderable_text() -> None:
    """A prompt should resolve to ordinary text for the existing renderer."""
    result = select_text_for_rendering(
        text=None,
        prompt="write a short thank-you note to my professor",
    )

    assert result.generated_text == "Thank you for your guidance and support."
    assert isinstance(result.generated_text, str)
    assert result.generated_text.strip()


def test_missing_text_and_prompt_raises_clear_error() -> None:
    """The pipeline should reject a request with no text source."""
    with pytest.raises(ValueError, match="one of --text or --prompt"):
        select_text_for_rendering(text=None, prompt=None)


def test_text_and_prompt_together_raise_clear_error() -> None:
    """Ambiguous direct and generated text should be rejected."""
    with pytest.raises(ValueError, match="either --text or --prompt, not both"):
        select_text_for_rendering(text="hello", prompt="write hello")


def test_external_provider_is_an_explicit_placeholder() -> None:
    """Unimplemented providers should fail without network access or dependencies."""
    with pytest.raises(NotImplementedError, match="not implemented"):
        generate_text_from_prompt("write a note", provider="openai")
