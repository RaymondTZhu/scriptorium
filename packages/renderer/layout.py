"""Layout settings for glyph-based handwritten-style rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderSettings:
    """Basic rendering settings for V1 handwritten-style output."""

    canvas_width: int = 1200
    canvas_height: int = 500
    margin_left: int = 60
    margin_top: int = 80
    line_height: int = 95
    glyph_height: int = 70
    character_spacing: int = 8
    word_spacing: int = 38
    baseline_jitter_px: int = 3
    placeholder_width: int = 36
