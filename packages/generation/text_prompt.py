"""Deterministic prompt-to-text generation for handwriting rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedTextResult:
    """Text selected or generated for the glyph-based renderer."""

    prompt: str
    generated_text: str
    provider: str
    model: str | None
    used_fallback: bool


def generate_text_from_prompt(
    prompt: str,
    provider: str = "local",
) -> GeneratedTextResult:
    """Generate short text from a prompt without requiring network access."""
    normalized_prompt = " ".join(prompt.strip().split())
    if not normalized_prompt:
        raise ValueError("Prompt must contain non-whitespace text.")

    normalized_provider = provider.strip().lower()
    if normalized_provider != "local":
        raise NotImplementedError(
            f"Text provider {provider!r} is not implemented. Use --text-provider local."
        )

    prompt_words = set(re.findall(r"[a-z]+", normalized_prompt.lower()))
    generated_text = _generate_local_text(normalized_prompt, prompt_words)

    return GeneratedTextResult(
        prompt=normalized_prompt,
        generated_text=generated_text,
        provider="local",
        model=None,
        used_fallback=False,
    )


def select_text_for_rendering(
    *,
    text: str | None,
    prompt: str | None,
    provider: str = "local",
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

    return generate_text_from_prompt(prompt or "", provider=provider)


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
