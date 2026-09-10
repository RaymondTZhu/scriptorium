"""Tests for offline and optional prompt-to-text selection."""

import json
import shutil
import sys
from types import SimpleNamespace

import pytest

from packages.common.paths import PROJECT_ROOT
from packages.generation import (
    generate_text_from_prompt,
    select_text_for_rendering,
    text_generation_metadata,
)
from packages.watermark.metadata import write_generation_manifest


TEST_SCRATCH_DIR = PROJECT_ROOT / ".tmp_tests" / "text_generation"


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


def test_openai_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenAI selection should give a clear error before importing the optional SDK."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is required"):
        generate_text_from_prompt("write a note", provider="openai")


def test_openai_provider_uses_mocked_responses_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """The optional provider should use Responses API output without a network call."""
    captured: dict = {}

    class FakeResponses:
        def create(self, **kwargs: object) -> SimpleNamespace:
            captured.update(kwargs)
            return SimpleNamespace(output_text="  A generated note for rendering.  ")

    fake_client = SimpleNamespace(responses=FakeResponses())
    fake_module = SimpleNamespace(OpenAI=lambda: fake_client)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    result = generate_text_from_prompt(
        "write a note",
        provider="openai",
        model="gpt-5.5",
        max_chars=12,
    )

    assert result.generated_text == "A generated"
    assert result.provider == "openai"
    assert result.model == "gpt-5.5"
    assert captured["model"] == "gpt-5.5"
    assert captured["input"] == "write a note"
    assert "only the short final text" in str(captured["instructions"])


def test_prompt_generation_fields_are_written_to_manifest() -> None:
    """Generation records should retain prompt, provider, model, and length metadata."""
    if TEST_SCRATCH_DIR.exists():
        shutil.rmtree(TEST_SCRATCH_DIR)
    TEST_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    result = generate_text_from_prompt("write a thank you note", max_chars=120)
    try:
        manifest_path = write_generation_manifest(
            user_id="test_user",
            input_text=result.generated_text,
            output_image_path=TEST_SCRATCH_DIR / "rendered.png",
            manifest_dir=TEST_SCRATCH_DIR,
            extra_fields=text_generation_metadata(result, 120),
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["source_prompt"] == "write a thank you note"
        assert manifest["generated_text"] == result.generated_text
        assert manifest["text_provider"] == "local"
        assert manifest["text_model"] is None
        assert manifest["used_text_generation_fallback"] is False
        assert manifest["max_generated_chars"] == 120
    finally:
        shutil.rmtree(PROJECT_ROOT / ".tmp_tests", ignore_errors=True)
