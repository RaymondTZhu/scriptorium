"""Deterministic prompt-to-text generation for handwriting rendering."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


DEFAULT_OPENAI_TEXT_MODEL = "gpt-5.5"


@dataclass(frozen=True)
class GeneratedTextResult:
    """Text selected or generated for the glyph-based renderer."""

    prompt: str
    generated_text: str
    provider: str
    model: str | None
    used_fallback: bool
    error: str | None = None


def generate_text_from_prompt(
    prompt: str,
    provider: str = "local",
    model: str | None = None,
    max_chars: int = 500,
) -> GeneratedTextResult:
    """Generate text from a local rule or the optional OpenAI provider.

    Generated output longer than ``max_chars`` is truncated before rendering.
    """
    normalized_prompt = " ".join(prompt.strip().split())
    if not normalized_prompt:
        raise ValueError("Prompt must contain non-whitespace text.")
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    normalized_provider = provider.strip().lower()
    if normalized_provider == "local":
        prompt_words = set(re.findall(r"[a-z]+", normalized_prompt.lower()))
        generated_text = _truncate_text(
            _generate_local_text(normalized_prompt, prompt_words),
            max_chars,
        )
        active_model = None
    elif normalized_provider == "openai":
        generated_text, active_model = _generate_openai_text(
            normalized_prompt,
            model=model,
            max_chars=max_chars,
        )
    else:
        raise ValueError(
            f"Unknown text provider {provider!r}. Choose 'local' or 'openai'."
        )

    return GeneratedTextResult(
        prompt=normalized_prompt,
        generated_text=generated_text,
        provider=normalized_provider,
        model=active_model,
        used_fallback=False,
    )


def select_text_for_rendering(
    *,
    text: str | None,
    prompt: str | None,
    provider: str = "local",
    model: str | None = None,
    max_chars: int = 500,
) -> GeneratedTextResult:
    """Select direct text or generate it from exactly one prompt input."""
    has_text = text is not None and bool(text.strip())
    has_prompt = prompt is not None and bool(prompt.strip())

    if has_text and has_prompt:
        raise ValueError("Provide either --text or --prompt, not both.")
    if not has_text and not has_prompt:
        raise ValueError("Provide one of --text or --prompt.")

    if has_text:
        return GeneratedTextResult(
            prompt="",
            generated_text=text.strip(),
            provider="direct",
            model=None,
            used_fallback=False,
        )

    return generate_text_from_prompt(
        prompt or "",
        provider=provider,
        model=model,
        max_chars=max_chars,
    )


def text_generation_metadata(
    result: GeneratedTextResult,
    max_generated_chars: int,
) -> dict[str, str | int | bool | None]:
    """Return traceability fields for a selected or generated text result."""
    return {
        "source_prompt": result.prompt or None,
        "generated_text": result.generated_text,
        "text_provider": result.provider,
        "text_model": result.model,
        "used_text_generation_fallback": result.used_fallback,
        "max_generated_chars": max_generated_chars,
    }


def _generate_openai_text(
    prompt: str,
    *,
    model: str | None,
    max_chars: int,
) -> tuple[str, str]:
    """Generate final renderable text with the optional OpenAI SDK."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is required for --text-provider openai. "
            "Set it in the environment before running the command."
        )

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError(
            "The optional OpenAI SDK is not installed. Install it with "
            "python -m pip install -e \".[ai]\"."
        ) from error

    active_model = model or DEFAULT_OPENAI_TEXT_MODEL
    client = OpenAI()
    try:
        response = client.responses.create(
            model=active_model,
            instructions=(
                "Produce only the short final text that should be rendered. "
                "Do not include explanations, labels, markdown, or quotation marks."
            ),
            input=prompt,
        )
    except Exception as error:
        raise RuntimeError(f"OpenAI text generation failed: {error}") from error

    generated_text = _truncate_text(response.output_text, max_chars)
    if not generated_text:
        raise RuntimeError("OpenAI returned no text to render.")

    return generated_text, active_model


def _truncate_text(text: str, max_chars: int) -> str:
    """Trim and truncate generated text to the configured character limit."""
    return text.strip()[:max_chars].rstrip()


def _generate_local_text(normalized_prompt: str, prompt_words: set[str]) -> str:
    """Return deterministic text from a small transparent set of local rules."""
    if "thank" in prompt_words and "professor" in prompt_words:
        return "Thank you for your guidance and support."
    if "thank" in prompt_words:
        return "Thank you for your time and support."
    if "congratulate" in prompt_words or "congratulations" in prompt_words:
        return "Congratulations on your wonderful achievement!"
    if "apology" in prompt_words or "apologize" in prompt_words:
        return "I am sorry, and I appreciate your understanding."

    text = re.sub(
        r"^(?:please\s+)?(?:write|draft|create)\s+(?:a\s+)?",
        "",
        normalized_prompt,
        flags=re.IGNORECASE,
    ).strip(" .")
    if not text:
        text = "A short handwritten note"
    text = text[:157].rstrip()
    return f"{text[0].upper()}{text[1:]}."
